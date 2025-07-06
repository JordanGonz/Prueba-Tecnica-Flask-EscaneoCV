import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import Candidate
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.text_cleaner import clean_and_extract_info
from parsers.vision_parser import extract_cv_data_with_vision, generate_text_embedding,search_candidates_semantic
from storage.sqlite_handler import search_candidates, get_all_candidates
from sqlalchemy import or_
from flask import request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import traceback


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

logger = logging.getLogger(__name__)

routes_bp = Blueprint('routes', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes_bp.route('/')
def index():
    total_candidates = db.session.query(Candidate).count()
    recent_candidates = db.session.query(Candidate).order_by(Candidate.created_at.desc()).limit(5).all()
    return render_template('index.html', total_candidates=total_candidates, recent_candidates=recent_candidates)

@routes_bp.route('/upload', methods=['GET', 'POST'])
def upload_cv():
    if request.method == 'POST':
        if 'cv_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['cv_file']
        if not file.filename or not allowed_file(file.filename):
            flash('Invalid or missing file', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename or 'unknown')
        file_ext = filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        try:
            # Guardar archivo
            file.save(filepath)

            # Extraer texto plano
            extracted_text = ""
            if file_ext == 'pdf':
                extracted_text = extract_text_from_pdf(filepath)
            elif file_ext == 'docx':
                extracted_text = extract_text_from_docx(filepath)
            elif file_ext == 'txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()

            if not extracted_text.strip():
                os.remove(filepath)
                flash('No se pudo extraer texto del archivo.', 'error')
                return redirect(request.url)

            # Intentar extracción con visión
            vision_data = {}
            try:
                vision_data = extract_cv_data_with_vision(filepath, file_ext)
            except Exception as ve:
                logger.warning(f"Vision fallback: {str(ve)}")

            # Fallback a parser de texto si vision_data está vacío
            if not vision_data or not any(vision_data.values()):
                candidate_info = clean_and_extract_info(extracted_text)
            else:
                candidate_info = {
                    'name': vision_data.get('name', 'Unknown'),
                    'email': vision_data.get('email', ''),
                    'phone': vision_data.get('phone', ''),
                    'education': json.dumps(vision_data.get('education', [])),
                    'experience': json.dumps(vision_data.get('experience', [])),
                    'skills': json.dumps(vision_data.get('skills', []))
                }

            # Crear texto base para el embedding
            embedding_text = " ".join(filter(None, [
                candidate_info.get('name', ''),
                candidate_info.get('skills', ''),
                candidate_info.get('experience', ''),
                extracted_text[:1500]  # Controla el tamaño del input
            ])).replace("\n", " ")

            # Generar embedding
            embedding = []
            try:
                embedding = generate_text_embedding(embedding_text)
            except Exception as ee:
                logger.warning(f"Error embedding: {str(ee)}")

            # Crear candidato
            candidate = Candidate(
                name=candidate_info.get('name', 'Unknown'),
                email=candidate_info.get('email', ''),
                phone=candidate_info.get('phone', ''),
                education=candidate_info.get('education', ''),
                experience=candidate_info.get('experience', ''),
                skills=candidate_info.get('skills', ''),
                languages=json.dumps(vision_data.get('languages', [])),
                certifications=json.dumps(vision_data.get('certifications', [])),
                summary=vision_data.get('summary', ''),
                vision_analysis=json.dumps(vision_data),
                text_embedding=json.dumps(embedding),
                full_text=extracted_text,
                original_filename=filename,
                file_type=file_ext
            )

            db.session.add(candidate)
            db.session.commit()

            # Opcional: guardar vector si usas Pinecone u otro servicio externo
            if embedding:
                from storage.vector_search import store_embedding_vector
                store_embedding_vector(candidate.id, embedding)

            os.remove(filepath)
            flash(f"CV cargado correctamente. Candidato: {candidate.name}", 'success')
            return redirect(url_for('routes.view_candidate', candidate_id=candidate.id))

        except Exception as e:
            logger.error(f"Error procesando CV {filename}: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f"Error procesando archivo: {str(e)}", 'error')
            return redirect(request.url)

    return render_template('upload.html')


@routes_bp.route('/search', methods=['GET', 'POST'])
def search():
    candidates = []
    search_query = ""

    if request.method == 'POST':
        # Soporta tanto formularios clásicos como JSON enviado desde JS
        if request.is_json:
            data = request.get_json()
            search_query = data.get('query', '').strip()
        else:
            search_query = request.form.get('search_query', '').strip()

        if search_query:
            try:
                candidates = search_candidates(search_query)
                if not candidates:
                    flash(f'No candidates found for "{search_query}"', 'info')
                else:
                    flash(f'Found {len(candidates)} candidate(s) for "{search_query}"', 'success')
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}")
                flash(f'Error performing search: {str(e)}', 'error')
        else:
            flash('Please enter a search query', 'error')

    return render_template('search_new.html', candidates=candidates, search_query=search_query)


@routes_bp.route('/candidates')
def candidates():
    try:
        all_candidates = get_all_candidates()
        return render_template('candidates.html', candidates=all_candidates)
    except Exception as e:
        logger.error(f"Error fetching candidates: {str(e)}")
        flash(f'Error fetching candidates: {str(e)}', 'error')
        return render_template('candidates.html', candidates=[])

@routes_bp.route('/candidate/<int:candidate_id>')
def view_candidate(candidate_id):
    try:
        candidate = db.session.get(Candidate, candidate_id)
        if not candidate:
            flash('Candidate not found', 'error')
            return redirect(url_for('routes.candidates'))
        return render_template('candidate_detail.html', candidate=candidate)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {str(e)}")
        flash(f'Error fetching candidate: {str(e)}', 'error')
        return redirect(url_for('routes.candidates'))

@routes_bp.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
def delete_candidate(candidate_id):
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        candidate_name = candidate.name
        db.session.delete(candidate)
        db.session.commit()
        flash(f'Candidato {candidate_name} eliminado exitosamente', 'success')
        return jsonify({'success': True, 'message': 'Candidato eliminado'})
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    

@routes_bp.route('/search-api', methods=['POST'])
def search_api():
    candidates = []
    search_query = ""

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            search_query = data.get('query', '').strip()

            try:
                if search_query:
                    candidates = search_candidates(search_query)
                else:
                    candidates = get_all_candidates(limit=100)

                return jsonify({
                    "status": "success",
                    "query": search_query,
                    "count": len(candidates),
                    "candidates": [c.to_dict() for c in candidates]
                })
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}")
                return jsonify({"status": "error", "message": str(e)}), 500

        else:
            # Petición clásica desde HTML
            search_query = request.form.get('search_query', '').strip()
            try:
                if search_query:
                    candidates = search_candidates(search_query)
                    flash(f'Found {len(candidates)} candidate(s) for "{search_query}"', 'success' if candidates else 'info')
                else:
                    candidates = get_all_candidates(limit=100)
                    flash(f'Most recent {len(candidates)} candidates loaded', 'info')
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}")
                flash(f'Error performing search: {str(e)}', 'error')

    return render_template('search_new.html', candidates=candidates, search_query=search_query)


@routes_bp.route('/api/candidates-vectors-detailed', methods=['GET'])
def candidates_vectors_detailed():
    try:
        candidates = Candidate.query.all()

        return jsonify({
            "status": "success",
            "candidates": [c.to_dict() for c in candidates]
        })

    except Exception as e:
        logger.error(f"Error fetching detailed candidate vectors: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



@routes_bp.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('routes.upload_cv'))

@routes_bp.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@routes_bp.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return render_template('500.html'), 500