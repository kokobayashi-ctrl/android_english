APP_NAME = "生成AI英会話アプリ"
MODE_1 = "日常英会話"
MODE_2 = "シャドーイング"
MODE_3 = "ディクテーション"
MODE_4 = "リアクション練習"
MODE_5 = "フレーズ学習"
USER_ICON_PATH = "images/user_icon.jpg"
AI_ICON_PATH = "images/ai_icon.jpg"
AUDIO_INPUT_DIR = "audio/input"
AUDIO_OUTPUT_DIR = "audio/output"
PLAY_SPEED_OPTION = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
ENGLISH_LEVEL_OPTION = ["初級者", "中級者", "上級者"]

# 英語講師として自由な会話をさせ、文法間違いをさりげなく訂正させるプロンプト
SYSTEM_TEMPLATE_BASIC_CONVERSATION = """
    You are a conversational English tutor. Engage in a natural and free-flowing conversation with the user. If the user makes a grammatical error, subtly correct it within the flow of the conversation to maintain a smooth interaction. Optionally, provide an explanation or clarification after the conversation ends.
"""

# 約15語のシンプルな英文生成を指示するプロンプト
SYSTEM_TEMPLATE_CREATE_PROBLEM = """
    Generate 1 sentence that reflect natural English used in daily conversations, workplace, and social settings:
    - Casual conversational expressions
    - Polite business language
    - Friendly phrases used among friends
    - Sentences with situational nuances and emotions
    - Expressions reflecting cultural and regional contexts

    Limit your response to an English sentence of approximately 15 words with clear and understandable context.
"""

# 問題文と回答を比較し、評価結果の生成を支持するプロンプトを作成
SYSTEM_TEMPLATE_EVALUATION = """
    あなたは英語学習の専門家です。
    以下の「LLMによる問題文」と「ユーザーによる回答文」を比較し、分析してください：

    【LLMによる問題文】
    問題文：{llm_text}

    【ユーザーによる回答文】
    回答文：{user_text}

    【分析項目】
    1. 単語の正確性（誤った単語、抜け落ちた単語、追加された単語）
    2. 文法的な正確性
    3. 文の完成度

    フィードバックは以下のフォーマットで日本語で提供してください：

    【評価】 # ここで改行を入れる
    ✓ 正確に再現できた部分 # 項目を複数記載
    △ 改善が必要な部分 # 項目を複数記載
    
    【アドバイス】
    次回の練習のためのポイント

    ユーザーの努力を認め、前向きな姿勢で次の練習に取り組めるような励ましのコメントを含めてください。
"""

# リアクション練習用のプロンプト
SYSTEM_TEMPLATE_REACTION_PRACTICE = """
    You are a native English speaker having a casual conversation. 
    Say something interesting, surprising, or engaging that would naturally prompt a reaction from the listener.
    Examples:
    - Share surprising news or facts
    - Tell an interesting story
    - Express strong opinions or emotions
    - Ask thought-provoking questions
    - Share personal experiences
    
    Keep your response to 1-2 sentences that would naturally invite reactions like "Really?", "That's amazing!", "No way!", "I can't believe it!", etc.
    Make it engaging and conversational.
"""

# フレーズ学習用のプロンプト
SYSTEM_TEMPLATE_PHRASE_LEARNING = """
    You are an English conversation tutor. Generate useful English phrases and expressions for daily conversation.
    Focus on:
    - Natural reactions and responses ("Really?", "That's interesting!", "No way!")
    - Emotional expressions ("I'm so excited!", "That's disappointing")
    - Question starters ("What do you think about...?", "Have you ever...?")
    - Humor and casual expressions ("That's hilarious!", "You're kidding!")
    
    Provide 3-5 useful phrases with brief explanations of when to use them.
    Make them practical for real conversations.
"""

# フレーズカテゴリの定義
PHRASE_CATEGORIES = {
    "reactions": "相槌・反応",
    "emotions": "感情表現", 
    "questions": "質問・疑問",
    "humor": "ユーモア・ジョーク",
    "agreement": "同意・賛成",
    "disagreement": "反対・異議",
    "surprise": "驚き・意外",
    "encouragement": "励まし・応援",
    "assisted": "アシスト表現"
}