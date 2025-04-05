import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from image_utils import process_image
from ad_analyzer import analyze_ad_creative

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('ファイルがアップロードされていません', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if the file is selected
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('index'))
    
    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        flash(f'ファイル形式が許可されていません。アップロード可能な形式: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        return redirect(url_for('index'))

    # File size check
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        flash('ファイルサイズが10MBを超えています', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Process the image: resize and convert to base64 string using image_utils
        img_base64 = process_image(file)
        
        # Analyze the image using ad_analyzer module
        analysis_result = analyze_ad_creative(img_base64)
        
        return render_template('index.html', analysis=analysis_result, image_data=img_base64)
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        flash(f'画像処理中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
