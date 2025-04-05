import os
import json
import logging
from openai import OpenAI

logging.basicConfig(level=logging.DEBUG)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY environment variable not set!")

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_ad_creative(image_base64):
    """
    広告クリエイティブ画像をOpenAI APIを利用して分析する関数

    Parameters:
    - image_base64: 画像のbase64エンコード文字列

    Returns:
    - JSON形式の分析結果（文字列）
    """
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

    重要：各フィールドは適切にフォーマットされている必要があります。「strengths」、「weaknesses」、「improvement_suggestions」は
    各々少なくとも1つの要素を持つ配列としてください。
    """

    try:
        logging.debug("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
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
            max_tokens=1200
        )
    
        content = response.choices[0].message.content
        logging.debug(f"Response received: {content[:100]}...")

        analysis = json.loads(content)

        # 必須フィールドの検証
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
                
        for field in ["strengths", "weaknesses", "improvement_suggestions"]:
            if not analysis[field]:
                analysis[field] = ["Not specified"]

        return json.dumps(analysis)
    except Exception as e:
        logging.error(f"Error analyzing image: {str(e)}")
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
