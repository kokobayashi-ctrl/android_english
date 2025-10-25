import streamlit as st
import os
import time
from time import sleep
from pathlib import Path
from streamlit.components.v1 import html
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from openai import OpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import functions as ft
import constants as ct


# 各種設定
load_dotenv()
st.set_page_config(
    page_title=ct.APP_NAME
)

# タイトル表示
st.markdown(f"## {ct.APP_NAME}")

# 初期処理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.shadowing_evaluation_first_flg = True
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.dictation_chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""
    st.session_state.learned_phrases = []
    st.session_state.reaction_practice_flg = False
    st.session_state.phrase_learning_flg = False
    st.session_state.assistance_flg = False
    st.session_state.japanese_voice_input = ""
    st.session_state.japanese_voice_processed = False
    
    st.session_state.openai_obj = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    st.session_state.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)
    st.session_state.memory = ConversationSummaryBufferMemory(
        llm=st.session_state.llm,
        max_token_limit=1000,
        return_messages=True
    )

    # モード「日常英会話」用のChain作成
    st.session_state.chain_basic_conversation = ft.create_chain(ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION)

# 初期表示
# col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
# 提出課題用
col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
with col1:
    if st.session_state.start_flg:
        st.button("開始", use_container_width=True, type="primary")
    else:
        st.session_state.start_flg = st.button("開始", use_container_width=True, type="primary")
with col2:
    st.session_state.speed = st.selectbox(label="再生速度", options=ct.PLAY_SPEED_OPTION, index=3, label_visibility="collapsed")
with col3:
    st.session_state.mode = st.selectbox(label="モード", options=[ct.MODE_1, ct.MODE_2, ct.MODE_3, ct.MODE_4, ct.MODE_5], label_visibility="collapsed")
    # モードを変更した際の処理
    if st.session_state.mode != st.session_state.pre_mode:
        # 自動でそのモードの処理が実行されないようにする
        st.session_state.start_flg = False
        # 「日常英会話」選択時の初期化処理
        if st.session_state.mode == ct.MODE_1:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # 「シャドーイング」選択時の初期化処理
        st.session_state.shadowing_count = 0
        if st.session_state.mode == ct.MODE_2:
            st.session_state.dictation_flg = False
        # 「ディクテーション」選択時の初期化処理
        st.session_state.dictation_count = 0
        if st.session_state.mode == ct.MODE_3:
            st.session_state.shadowing_flg = False
        # 「リアクション練習」選択時の初期化処理
        if st.session_state.mode == ct.MODE_4:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # 「フレーズ学習」選択時の初期化処理
        if st.session_state.mode == ct.MODE_5:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # チャット入力欄を非表示にする
        st.session_state.chat_open_flg = False
    st.session_state.pre_mode = st.session_state.mode
with col4:
    st.session_state.englv = st.selectbox(label="英語レベル", options=ct.ENGLISH_LEVEL_OPTION, label_visibility="collapsed")

# アシスト機能のUI（常に表示）
st.divider()
with st.expander("🆘 英語表現アシスト機能", expanded=False):
    st.info("英語で表現できない時は、日本語で要望を入力してください。AIが適切な英語表現を提案します。")
    
    # 入力方法の選択
    input_method = st.radio(
        "入力方法を選択してください",
        ["📝 テキスト入力", "🎤 音声入力"],
        horizontal=True,
        key="assistance_input_method"
    )
    
    if input_method == "📝 テキスト入力":
        col1, col2 = st.columns([3, 1])
        with col1:
            japanese_request = st.text_input(
                "日本語で要望を入力してください",
                placeholder="例: 「お疲れ様です」を英語で言いたい",
                key="japanese_assistance_input"
            )
        with col2:
            assistance_button = st.button("🔍 英語表現を提案", use_container_width=True)
    
    else:  # 音声入力
        st.markdown("**音声入力で日本語の要望を話してください**")
        
        # 音声入力ボタン
        if st.button("🎤 日本語で音声入力", use_container_width=True, type="primary", key="japanese_voice_button"):
            # 音声入力を受け取って音声ファイルを作成
            audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/japanese_audio_input_{int(time.time())}.wav"
            ft.record_audio(audio_input_file_path)
            
            # 音声入力ファイルから日本語文字起こしテキストを取得
            with st.spinner('日本語音声をテキストに変換中...'):
                transcript = ft.transcribe_audio_japanese(audio_input_file_path)
                japanese_request = transcript.text
            
            # 音声入力テキストをセッション状態に保存
            st.session_state.japanese_voice_input = japanese_request
            st.session_state.japanese_voice_processed = True
            st.rerun()
        
        # 音声認識結果の表示
        if hasattr(st.session_state, 'japanese_voice_input') and st.session_state.japanese_voice_input:
            st.markdown("---")
            st.markdown("**🎯 音声認識結果**")
            st.info(f"「{st.session_state.japanese_voice_input}」")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔍 この内容で英語表現を提案", use_container_width=True, key="use_voice_input", type="primary"):
                    japanese_request = st.session_state.japanese_voice_input
                    assistance_button = True
                else:
                    assistance_button = False
            with col2:
                if st.button("🔄 音声入力をやり直す", use_container_width=True, key="retry_voice_input"):
                    if hasattr(st.session_state, 'japanese_voice_input'):
                        del st.session_state.japanese_voice_input
                    if hasattr(st.session_state, 'japanese_voice_processed'):
                        del st.session_state.japanese_voice_processed
                    st.rerun()
        else:
            assistance_button = False
    
    if assistance_button and japanese_request:
        with st.spinner("英語表現を生成中..."):
            assistance_result = ft.get_english_assistance(japanese_request)
        
        st.markdown("**英語表現の提案:**")
        st.markdown(assistance_result)
        
        # 提案された表現を学習フレーズとして保存するオプション
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 この表現を学習フレーズに追加", key="save_assisted_phrase"):
                # 基本表現を抽出して保存（簡単な実装）
                lines = assistance_result.split('\n')
                basic_phrase = ""
                for line in lines:
                    if "【基本表現】" in line or (line.strip().startswith('-') and not line.strip().startswith('【')):
                        basic_phrase = line.strip().replace('- ', '').replace('【基本表現】', '').strip()
                        if basic_phrase:
                            break
                
                if basic_phrase:
                    ft.save_assisted_phrase(basic_phrase, japanese_request, "アシスト機能で生成")
                    st.success("学習フレーズに追加しました！")
                    st.rerun()
                else:
                    st.warning("基本表現を抽出できませんでした。手動で追加してください。")
        
        with col2:
            if st.button("🔊 音声で練習", key="practice_assisted_phrase"):
                # 基本表現を抽出して音声再生
                lines = assistance_result.split('\n')
                basic_phrase = ""
                for line in lines:
                    if "【基本表現】" in line or (line.strip().startswith('-') and not line.strip().startswith('【')):
                        basic_phrase = line.strip().replace('- ', '').replace('【基本表現】', '').strip()
                        if basic_phrase:
                            break
                
                if basic_phrase:
                    with st.spinner("音声を生成中..."):
                        phrase_audio = st.session_state.openai_obj.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input=basic_phrase
                        )
                        temp_audio_path = f"{ct.AUDIO_OUTPUT_DIR}/temp_assisted_phrase.wav"
                        ft.save_to_wav(phrase_audio.content, temp_audio_path)
                        ft.play_wav(temp_audio_path, speed=st.session_state.speed)
                    st.success(f"「{basic_phrase}」を音声で練習しました！")
                else:
                    st.warning("基本表現を抽出できませんでした。")
        
        # メッセージリストに追加
        st.session_state.messages.append({"role": "user", "content": f"【日本語要望】{japanese_request}"})
        st.session_state.messages.append({"role": "assistant", "content": assistance_result})

with st.chat_message("assistant", avatar="images/ai_icon.jpg"):
    st.markdown("こちらは生成AIによる音声英会話の練習アプリです。何度も繰り返し練習し、英語力をアップさせましょう。")
    st.markdown("**【操作説明】**")
    st.success("""
    - モードと再生速度を選択し、「英会話開始」ボタンを押して英会話を始めましょう。
    - モードは「日常英会話」「シャドーイング」「ディクテーション」「リアクション練習」「フレーズ学習」から選べます。
    - 発話後、5秒間沈黙することで音声入力が完了します。
    - 「一時中断」ボタンを押すことで、英会話を一時中断できます。
    """)
st.divider()

# サイドバーに学習したフレーズを表示
with st.sidebar:
    st.header("📚 学習したフレーズ")
    
    if "learned_phrases" in st.session_state and st.session_state.learned_phrases:
        # カテゴリ別表示
        selected_category = st.selectbox(
            "カテゴリでフィルタ",
            ["全て"] + list(ct.PHRASE_CATEGORIES.keys()),
            key="phrase_category_filter"
        )
        
        # フレーズ一覧表示
        phrases_to_show = st.session_state.learned_phrases
        if selected_category != "全て":
            phrases_to_show = [p for p in st.session_state.learned_phrases if p["category"] == selected_category]
        
        for i, phrase_data in enumerate(phrases_to_show):
            with st.expander(f"{phrase_data['phrase'][:30]}...", expanded=False):
                st.write(f"**フレーズ**: {phrase_data['phrase']}")
                st.write(f"**カテゴリ**: {ct.PHRASE_CATEGORIES.get(phrase_data['category'], phrase_data['category'])}")
                st.write(f"**学習日**: {phrase_data['learned_date'][:10]}")
                st.write(f"**練習回数**: {phrase_data['practice_count']}")
                
                # 習得度の更新
                mastery_level = st.selectbox(
                    "習得度",
                    [0, 1, 2],
                    index=phrase_data['mastery_level'],
                    key=f"mastery_{i}",
                    format_func=lambda x: ["未習得", "学習中", "習得済み"][x]
                )
                
                if mastery_level != phrase_data['mastery_level']:
                    ft.update_phrase_mastery(phrase_data['phrase'], mastery_level)
                    st.rerun()
                
                # フレーズの音声再生
                if st.button(f"🔊 音声再生", key=f"play_{i}"):
                    phrase_audio = st.session_state.openai_obj.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=phrase_data['phrase']
                    )
                    temp_audio_path = f"{ct.AUDIO_OUTPUT_DIR}/temp_phrase_{i}.wav"
                    ft.save_to_wav(phrase_audio.content, temp_audio_path)
                    ft.play_wav(temp_audio_path, speed=st.session_state.speed)
    else:
        st.info("まだ学習したフレーズがありません。フレーズ学習モードで新しいフレーズを学習しましょう！")
    
    # 学習統計
    if "learned_phrases" in st.session_state and st.session_state.learned_phrases:
        st.header("📊 学習統計")
        stats = ft.get_phrase_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("総フレーズ数", stats['total'])
        with col2:
            mastered = stats['mastery_levels']['2']
            st.metric("習得済み", mastered)
        
        # カテゴリ別グラフ
        if stats['by_category']:
            st.bar_chart(stats['by_category'])

# メッセージリストの一覧表示
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="images/ai_icon.jpg"):
            st.markdown(message["content"])
    elif message["role"] == "user":
        with st.chat_message(message["role"], avatar="images/user_icon.jpg"):
            st.markdown(message["content"])
    else:
        st.divider()

# LLMレスポンスの下部にモード実行のボタン表示
if st.session_state.shadowing_flg:
    st.session_state.shadowing_button_flg = st.button("シャドーイング開始")
if st.session_state.dictation_flg:
    st.session_state.dictation_button_flg = st.button("ディクテーション開始")

# 「ディクテーション」モードのチャット入力受付時に実行
if st.session_state.chat_open_flg:
    st.info("AIが読み上げた音声を、画面下部のチャット欄からそのまま入力・送信してください。")

st.session_state.dictation_chat_message = st.chat_input("※「ディクテーション」選択時以外は送信不可")

if st.session_state.dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# 「英会話開始」ボタンが押された場合の処理
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (st.session_state.dictation_button_flg or st.session_state.dictation_count == 0 or st.session_state.dictation_chat_message):
        if st.session_state.dictation_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.dictation_first_flg = False
        # チャット入力以外
        if not st.session_state.chat_open_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()

            st.session_state.chat_open_flg = True
            st.session_state.dictation_flg = False
            st.rerun()
        # チャット入力時の処理
        else:
            # チャット欄から入力された場合にのみ評価処理が実行されるようにする
            if not st.session_state.dictation_chat_message:
                st.stop()
            
            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(st.session_state.dictation_chat_message)

            # LLMが生成した問題文とチャット入力値をメッセージリストに追加
            st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
            st.session_state.messages.append({"role": "user", "content": st.session_state.dictation_chat_message})
            
            with st.spinner('評価結果の生成中...'):
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=st.session_state.dictation_chat_message
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
                llm_response_evaluation = ft.create_evaluation()
            
            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
            st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
            st.session_state.messages.append({"role": "other"})
            
            # 各種フラグの更新
            st.session_state.dictation_flg = True
            st.session_state.dictation_chat_message = ""
            st.session_state.dictation_count += 1
            st.session_state.chat_open_flg = False

            st.rerun()

    
    # モード：「日常英会話」
    if st.session_state.mode == ct.MODE_1:
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        ft.record_audio(audio_input_file_path)

        # 音声入力ファイルから文字起こしテキストを取得
        with st.spinner('音声入力をテキストに変換中...'):
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # 音声入力テキストの画面表示
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)

        with st.spinner("回答の音声読み上げ準備中..."):
            # ユーザー入力値をLLMに渡して回答取得
            llm_response = st.session_state.chain_basic_conversation.predict(input=audio_input_text)
            
            # LLMからの回答を音声データに変換
            llm_response_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=llm_response
            )

            # 一旦mp3形式で音声ファイル作成後、wav形式に変換
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            ft.save_to_wav(llm_response_audio.content, audio_output_file_path)

        # 音声ファイルの読み上げ
        ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

        # AIメッセージの画面表示とリストへの追加
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response)

        # ユーザー入力値とLLMからの回答をメッセージ一覧に追加
        st.session_state.messages.append({"role": "user", "content": audio_input_text})
        st.session_state.messages.append({"role": "assistant", "content": llm_response})


    # モード：「シャドーイング」
    # 「シャドーイング」ボタン押下時か、「英会話開始」ボタン押下時
    if st.session_state.mode == ct.MODE_2 and (st.session_state.shadowing_button_flg or st.session_state.shadowing_count == 0 or st.session_state.shadowing_audio_input_flg):
        if st.session_state.shadowing_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.shadowing_first_flg = False
        
        if not st.session_state.shadowing_audio_input_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()

        # 音声入力を受け取って音声ファイルを作成
        st.session_state.shadowing_audio_input_flg = True
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        ft.record_audio(audio_input_file_path)
        st.session_state.shadowing_audio_input_flg = False

        with st.spinner('音声入力をテキストに変換中...'):
            # 音声入力ファイルから文字起こしテキストを取得
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # AIメッセージとユーザーメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(st.session_state.problem)
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)
        
        # LLMが生成した問題文と音声入力値をメッセージリストに追加
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
        st.session_state.messages.append({"role": "user", "content": audio_input_text})

        with st.spinner('評価結果の生成中...'):
            if st.session_state.shadowing_evaluation_first_flg:
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=audio_input_text
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                st.session_state.shadowing_evaluation_first_flg = False
            # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
            llm_response_evaluation = ft.create_evaluation()
        
        # 評価結果のメッセージリストへの追加と表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response_evaluation)
        st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
        st.session_state.messages.append({"role": "other"})
        
        # 各種フラグの更新
        st.session_state.shadowing_flg = True
        st.session_state.shadowing_count += 1

        # 「シャドーイング」ボタンを表示するために再描画
        st.rerun()

    # モード：「リアクション練習」
    if st.session_state.mode == ct.MODE_4:
        if not st.session_state.reaction_practice_flg:
            # リアクション練習用のChain作成
            st.session_state.chain_reaction_practice = ft.create_reaction_practice_chain()
            st.session_state.reaction_practice_flg = True
        
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        ft.record_audio(audio_input_file_path)

        # 音声入力ファイルから文字起こしテキストを取得
        with st.spinner('音声入力をテキストに変換中...'):
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # 音声入力テキストの画面表示
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)

        with st.spinner("リアクション練習の準備中..."):
            # リアクションを促す発話を生成
            reaction_prompt = st.session_state.chain_reaction_practice.predict(input="")
            
            # リアクション発話を音声データに変換
            reaction_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=reaction_prompt
            )

            # 音声ファイルの作成と再生
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            ft.save_to_wav(reaction_audio.content, audio_output_file_path)
            ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

        # AIメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(reaction_prompt)

        # ユーザーのリアクションを評価し、適切なフレーズを提案
        with st.spinner("リアクション評価中..."):
            evaluation_prompt = f"""
            ユーザーのリアクション: "{audio_input_text}"
            元の発話: "{reaction_prompt}"
            
            このリアクションが適切かどうか評価し、より自然なリアクションフレーズを提案してください。
            また、このシチュエーションで使える他のリアクションフレーズも教えてください。
            
            もしユーザーのリアクションが不適切な場合や、より良い表現がある場合は、
            具体的な改善案と、なぜその表現が良いのかの理由も含めてください。
            """
            
            evaluation_response = st.session_state.openai_obj.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.7
            )
            
            evaluation_text = evaluation_response.choices[0].message.content

        # 評価結果の表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(evaluation_text)

        # 学習したフレーズを保存
        if "Really?" in audio_input_text or "That's" in audio_input_text or "No way!" in audio_input_text:
            ft.save_learned_phrase(audio_input_text, "reactions", f"リアクション練習での使用")

        # メッセージリストに追加
        st.session_state.messages.append({"role": "user", "content": audio_input_text})
        st.session_state.messages.append({"role": "assistant", "content": reaction_prompt})
        st.session_state.messages.append({"role": "assistant", "content": evaluation_text})

    # モード：「フレーズ学習」
    if st.session_state.mode == ct.MODE_5:
        if not st.session_state.phrase_learning_flg:
            # フレーズ学習用のChain作成
            st.session_state.chain_phrase_learning = ft.create_phrase_learning_chain()
            st.session_state.phrase_learning_flg = True
        
        with st.spinner("フレーズ生成中..."):
            # 新しいフレーズを生成
            new_phrases = st.session_state.chain_phrase_learning.predict(input="")
            
            # 生成されたフレーズを音声で読み上げ
            phrases_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=new_phrases
            )

            # 音声ファイルの作成と再生
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            ft.save_to_wav(phrases_audio.content, audio_output_file_path)
            ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

        # フレーズの表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(new_phrases)

        # フレーズをカテゴリ別に保存
        phrases_list = new_phrases.split('\n')
        for phrase in phrases_list:
            if phrase.strip() and not phrase.strip().startswith('#'):
                # カテゴリを自動判定（簡単な例）
                category = "reactions"
                if "?" in phrase:
                    category = "questions"
                elif "!" in phrase:
                    category = "emotions"
                elif "joke" in phrase.lower() or "funny" in phrase.lower():
                    category = "humor"
                
                ft.save_learned_phrase(phrase.strip(), category, "フレーズ学習で生成")

        # 学習統計の表示
        stats = ft.get_phrase_statistics()
        with st.expander("学習統計", expanded=False):
            st.write(f"**総学習フレーズ数**: {stats['total']}")
            st.write("**カテゴリ別**:")
            for category, count in stats['by_category'].items():
                st.write(f"- {ct.PHRASE_CATEGORIES.get(category, category)}: {count}")
            st.write("**習得度別**:")
            st.write(f"- 未習得: {stats['mastery_levels']['0']}")
            st.write(f"- 学習中: {stats['mastery_levels']['1']}")
            st.write(f"- 習得済み: {stats['mastery_levels']['2']}")

        # メッセージリストに追加
        st.session_state.messages.append({"role": "assistant", "content": new_phrases})