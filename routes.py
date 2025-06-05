import os
import json
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Candidate
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.text_cleaner import clean_and_extract_info
from parsers.vision_parser import extract_cv_data_with_vision, generate_text_embedding
from storage.sqlite_handler import search_candidates, get_all_candidates

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page showing recruitment system dashboard"""
    total_candidates = db.session.query(Candidate).count()
    recent_candidates = db.session.query(Candidate).order_by(Candidate.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_candidates=total_candidates,
                         recent_candidates=recent_candidates)

@app.route('/upload', methods=['GET', 'POST'])
def upload_cv():
    """Handle CV upload and processing"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'cv_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['cv_file']
        
        # Check if file was actually selected
        if not file.filename:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename or 'unknown')
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                # Save file temporarily
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract text based on file type
                extracted_text = ""
                if file_extension == 'pdf':
                    extracted_text = extract_text_from_pdf(filepath)
                elif file_extension == 'docx':
                    extracted_text = extract_text_from_docx(filepath)
                elif file_extension == 'txt':
                    with open(filepath, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                
                if not extracted_text.strip():
                    flash('Could not extract text from the file', 'error')
                    os.remove(filepath)
                    return redirect(request.url)
                
                # Try vision analysis first for better extraction
                vision_data = {}
                try:
                    vision_data = extract_cv_data_with_vision(filepath, file_extension)
                    logger.info(f"Vision analysis completed for {filename}")
                except Exception as e:
                    logger.warning(f"Vision analysis failed for {filename}: {str(e)}")
                
                # Fallback to traditional text extraction if vision fails
                if not vision_data:
                    candidate_info = clean_and_extract_info(extracted_text)
                else:
                    # Use vision data as primary source
                    candidate_info = {
                        'name': vision_data.get('name', 'Unknown'),
                        'email': vision_data.get('email', ''),
                        'phone': vision_data.get('phone', ''),
                        'education': str(vision_data.get('education', [])) if vision_data.get('education') else '',
                        'experience': str(vision_data.get('experience', [])) if vision_data.get('experience') else '',
                        'skills': str(vision_data.get('skills', [])) if vision_data.get('skills') else ''
                    }
                
                # Generate text embedding for semantic search
                embedding = []
                try:
                    search_text = f"{candidate_info.get('name', '')} {candidate_info.get('skills', '')} {candidate_info.get('experience', '')} {extracted_text[:1000]}"
                    embedding = generate_text_embedding(search_text)
                    logger.info(f"Generated embedding for {filename}")
                except Exception as e:
                    logger.warning(f"Embedding generation failed for {filename}: {str(e)}")
                
                # Create new candidate record
                candidate = Candidate(
                    name=vision_data.get('name', candidate_info.get('name', 'Unknown')),
                    email=vision_data.get('email', candidate_info.get('email', '')),
                    phone=vision_data.get('phone', candidate_info.get('phone', '')),
                    education=json.dumps(vision_data.get('education', [])) if vision_data.get('education') else '',
                    experience=json.dumps(vision_data.get('experience', [])) if vision_data.get('experience') else '',
                    skills=json.dumps(vision_data.get('skills', [])) if vision_data.get('skills') else '',
                    languages=json.dumps(vision_data.get('languages', [])) if vision_data.get('languages') else '',
                    certifications=json.dumps(vision_data.get('certifications', [])) if vision_data.get('certifications') else '',
                    summary=vision_data.get('summary', ''),
                    vision_analysis=json.dumps(vision_data) if vision_data else '',
                    text_embedding=json.dumps(embedding) if embedding else '',
                    full_text=extracted_text,
                    original_filename=filename,
                    file_type=file_extension
                )
                
                db.session.add(candidate)
                db.session.commit()
                
                # Store embedding in vector database if available
                if embedding:
                    from storage.vector_search import store_embedding_vector
                    store_embedding_vector(candidate.id, embedding)
                    logger.info(f"Stored vector embedding for candidate {candidate.id}")
                
                # Clean up temporary file
                os.remove(filepath)
                
                flash(f'CV uploaded successfully! Candidate: {candidate.name}', 'success')
                logger.info(f"Successfully processed CV: {filename} for candidate: {candidate.name}")
                
                return redirect(url_for('view_candidate', candidate_id=candidate.id))
                
            except Exception as e:
                logger.error(f"Error processing CV {filename}: {str(e)}")
                flash(f'Error processing CV: {str(e)}', 'error')
                
                # Clean up file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload PDF, DOCX, or TXT files only.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search for candidates"""
    candidates = []
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        
        if search_query:
            try:
                candidates = search_candidates(search_query)
                logger.info(f"Search performed for query: '{search_query}', found {len(candidates)} candidates")
                
                if not candidates:
                    flash(f'No candidates found for "{search_query}"', 'info')
                else:
                    flash(f'Found {len(candidates)} candidate(s) for "{search_query}"', 'success')
                    
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}")
                flash(f'Error performing search: {str(e)}', 'error')
        else:
            flash('Please enter a search query', 'error')
    
    return render_template('search_new.html', 
                         candidates=candidates, 
                         search_query=search_query)

@app.route('/candidates')
def candidates():
    """View all candidates"""
    try:
        all_candidates = get_all_candidates()
        return render_template('candidates.html', candidates=all_candidates)
    except Exception as e:
        logger.error(f"Error fetching candidates: {str(e)}")
        flash(f'Error fetching candidates: {str(e)}', 'error')
        return render_template('candidates.html', candidates=[])

@app.route('/candidate/<int:candidate_id>')
def view_candidate(candidate_id):
    """View individual candidate details"""
    try:
        candidate = db.session.get(Candidate, candidate_id)
        if not candidate:
            flash('Candidate not found', 'error')
            return redirect(url_for('candidates'))
        
        return render_template('candidate_detail.html', candidate=candidate)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {str(e)}")
        flash(f'Error fetching candidate: {str(e)}', 'error')
        return redirect(url_for('candidates'))

@app.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
def delete_candidate(candidate_id):
    """Delete a candidate"""
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        candidate_name = candidate.name
        
        db.session.delete(candidate)
        db.session.commit()
        
        flash(f'Candidato {candidate_name} eliminado exitosamente', 'success')
        logger.info(f"Deleted candidate: {candidate_name} (ID: {candidate_id})")
        
        return jsonify({'success': True, 'message': 'Candidato eliminado'})
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/candidates-vectors')
def api_candidates_vectors():
    """Get all candidates with their vector embeddings for visualization"""
    try:
        candidates = Candidate.query.filter(Candidate.text_embedding.isnot(None)).all()
        
        candidates_data = []
        for candidate in candidates:
            candidates_data.append({
                'id': candidate.id,
                'name': candidate.name,
                'email': candidate.email,
                'phone': candidate.phone,
                'skills': candidate.skills,
                'has_embedding': bool(candidate.text_embedding)
            })
        
        return jsonify({
            'candidates': candidates_data,
            'count': len(candidates_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching candidates vectors: {str(e)}")
        return jsonify({'error': str(e), 'candidates': []}), 500

@app.route('/api/candidates-vectors-detailed')
def api_candidates_vectors_detailed():
    """Get all candidates with detailed vector embeddings for advanced visualization"""
    try:
        candidates = Candidate.query.filter(Candidate.text_embedding.isnot(None)).all()
        candidates_data = []
        
        for candidate in candidates:
            candidate_dict = {
                'id': candidate.id,
                'name': candidate.name,
                'email': candidate.email,
                'skills': candidate.skills,
                'embedding': None,
                'embedding_magnitude': 0
            }
            
            # Include full embedding vector
            if candidate.text_embedding:
                try:
                    embedding = json.loads(candidate.text_embedding)
                    candidate_dict['embedding'] = embedding
                    # Calculate vector magnitude for visualization
                    magnitude = sum(x*x for x in embedding) ** 0.5
                    candidate_dict['embedding_magnitude'] = magnitude
                except:
                    pass
                
            candidates_data.append(candidate_dict)
        
        return jsonify({
            'candidates': candidates_data,
            'count': len(candidates_data),
            'embedding_dimensions': 1536 if candidates_data and candidates_data[0]['embedding'] else 0
        })
    except Exception as e:
        logger.error(f"Error fetching detailed candidates vectors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/semantic-search', methods=['POST'])
def api_semantic_search():
    """Perform high-performance semantic search using pgvector"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required', 'results': []}), 400
        
        # Generate embedding for search query
        from parsers.vision_parser import generate_text_embedding
        from storage.vector_search import vector_similarity_search
        
        query_embedding = generate_text_embedding(query)
        
        # Use pgvector for ultra-fast similarity search with lower threshold for better recall
        results = vector_similarity_search(query_embedding, limit=10, min_similarity=0.1)
        
        logger.info(f"Vector search for '{query}' returned {len(results)} results")
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return jsonify({'error': str(e), 'results': []}), 500

@app.route('/healthcheck')
def healthcheck():
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'OK', 'database': 'connected'}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('upload_cv'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return render_template('500.html'), 500
