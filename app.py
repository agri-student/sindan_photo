import os
import base64

import anthropic
import google.generativeai as genai
import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

SYSTEM_PROMPT = """あなたは農業の専門家です。ユーザーがアップロードした農作物の写真を分析し、以下の観点から生育状態を診断してください。

## 診断項目
1. **作物の種類**: 写真に写っている農作物を特定
2. **生育ステージ**: 現在の成長段階（発芽期・生長期・開花期・結実期・収穫期など）
3. **健康状態**: 総合的な健康度を5段階で評価（★1〜★5）
4. **葉の状態**: 色・形・大きさの異常の有無
5. **病害虫の兆候**: 病気や害虫被害の兆候の有無と、あれば具体的な病名・害虫名
6. **栄養状態**: 栄養過多・不足の兆候（窒素・リン・カリウムなど）
7. **アドバイス**: 今後の管理で注意すべき点や推奨される対策

## 回答形式
わかりやすい日本語で、農業初心者にも理解できるように回答してください。
写真が農作物でない場合は、その旨を伝えてください。"""


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "画像ファイルが選択されていません"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "画像ファイルが選択されていません"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "対応していないファイル形式です（PNG, JPG, GIF, WebP のみ）"}), 400

    image_data = file.read()
    base64_image = base64.b64encode(image_data).decode("utf-8")

    ext = file.filename.rsplit(".", 1)[1].lower()
    media_type_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_type_map[ext]

    provider = request.form.get("provider", "anthropic")
    user_text = "この農作物の写真を分析して、生育状態を診断してください。"

    try:
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{base64_image}"}},
                            {"type": "text", "text": user_text},
                        ],
                    },
                ],
            )
            result = response.choices[0].message.content
        elif provider == "google":
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
            response = model.generate_content([
                {"mime_type": media_type, "data": base64_image},
                user_text,
            ])
            result = response.text
        else:
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": user_text},
                        ],
                    }
                ],
            )
            result = message.content[0].text

        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"AI分析中にエラーが発生しました: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
