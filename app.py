import os
import base64
import logging
from io import BytesIO
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY environment variable not set!")

client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_ad_creative(image_base64):
    """
    Analyze the advertising creative image using OpenAI's GPT-4 Vision model
    """
    try:
        prompt = """
        この広告クリエイティブ画像を詳細に分析してください。あなたは専門の広告コンサルタントです。

        以下の点についてフィードバックを提供してください：
        1. 視覚的な魅力と明瞭さ
        2. メッセージの効果
        3. ターゲット層との適合性
        4. ブランドの一貫性
        5. CTAの効果
        6. 具体的な改善提案
        7. 推定CTR（クリック率）とCPA（獲得単価）および根拠

        応答は以下のセクションを含むJSONフォーマットで提供してください：
        {
            "overall_rating": [1-10のスコア],
            "strengths": [強みのリストを配列で],
            "weaknesses": [弱みのリストを配列で],
            "improvement_suggestions": [具体的で実行可能な提案を配列で],
            "target_audience": [このクリエイティブが訴求する対象者を文字列で],
            "effectiveness_score": [1-10のスコア],
            "estimated_ctr": [推定クリック率をパーセンテージで、例: "2.5%"],
            "estimated_cpa": [推定獲得単価を円で、例: "800円"],
            "ctr_reasoning": [CTR推定値の根拠を詳細に説明する文字列],
            "cpa_reasoning": [CPA推定値の根拠を詳細に説明する文字列]
        }

        重要：各フィールドは適切にフォーマットされている必要があります。"strengths"、"weaknesses"、"improvement_suggestions" 
        は各々少なくとも1つの要素を持つ配列であり、文字列やその他の形式ではないようにしてください。
        
        estimated_ctrとestimated_cpaについては、広告の業界標準と比較して、この広告クリエイティブがどの程度のパフォーマンスを
        見込めるかを専門的な視点から推定してください。実際の数値は提供できないため、見込まれる範囲で最も可能性の高い値を
        予測してください。ctr_reasoningとcpa_reasoningでは、その値に至った根拠を具体的に説明してください。
        業界平均や、広告のデザイン、メッセージ、ターゲット層などを考慮して詳細に解説してください。

        すべての応答は日本語で返してください。
        """
        
        logging.debug("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": "あなたは日本の広告業界の専門コンサルタントで、広告クリエイティブの分析と最適化のエキスパートです。マーケティング指標に基づいて詳細かつ実用的なアドバイスを提供します。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1200  # より詳細な分析のためにトークン数を増やす
        )
        
        content = response.choices[0].message.content
        logging.debug(f"Response received: {content[:100]}...")
        
        # Validate the JSON response
        import json
        analysis = json.loads(content)
        
        # Ensure all required fields exist and have the correct type
        required_fields = {
            "overall_rating": (int, float),
            "strengths": list,
            "weaknesses": list,
            "improvement_suggestions": list,
            "target_audience": str,
            "effectiveness_score": (int, float),
            "estimated_ctr": str,
            "estimated_cpa": str,
            "ctr_reasoning": str,
            "cpa_reasoning": str
        }
        
        for field, field_type in required_fields.items():
            if field not in analysis:
                analysis[field] = [] if field_type == list else "" if field_type == str else 0
            elif field in ["strengths", "weaknesses", "improvement_suggestions"] and not isinstance(analysis[field], list):
                analysis[field] = [str(analysis[field])]
        
        # Ensure lists have at least one item
        for field in ["strengths", "weaknesses", "improvement_suggestions"]:
            if not analysis[field]:
                analysis[field] = ["Not specified"]
        
        return json.dumps(analysis)
    except Exception as e:
        logging.error(f"Error analyzing image: {str(e)}")
        # Return a properly formatted error response
        error_response = {
            "error": f"画像の分析に失敗しました: {str(e)}",
            "overall_rating": 5,
            "strengths": ["エラーのため強みを分析できませんでした"],
            "weaknesses": ["エラーのため弱みを分析できませんでした"],
            "improvement_suggestions": ["別の画像をアップロードしてみてください"],
            "target_audience": "エラーのため判断できませんでした",
            "effectiveness_score": 5,
            "estimated_ctr": "エラーのため推定できません",
            "estimated_cpa": "エラーのため推定できません",
            "ctr_reasoning": "エラーが発生したため、CTRの根拠を提供できません。",
            "cpa_reasoning": "エラーが発生したため、CPAの根拠を提供できません。"
        }
        return json.dumps(error_response)

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
    
    # Check if the file is valid
    if file.filename == '':
        flash('ファイルが選択されていません', 'danger')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash(f'ファイル形式が許可されていません。アップロード可能な形式: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        return redirect(url_for('index'))

    # ファイルサイズチェックを追加
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        flash('ファイルサイズが10MBを超えています', 'danger')
        return redirect(url_for('index'))
    
    # Process the image
    try:
        # Read the image and convert to base64
        img = Image.open(file)
        
        # Resize if too large (to save bandwidth and tokens)
        max_size = 1024
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size))
        
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Analyze the image
        analysis_result = analyze_ad_creative(img_base64)
        
        return render_template('index.html', analysis=analysis_result, image_data=img_base64)
        
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        flash(f'画像処理中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
