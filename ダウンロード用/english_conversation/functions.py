import streamlit as st
import os
import time
from pathlib import Path
import wave
import pyaudio
from pydub import AudioSegment
from audiorecorder import audiorecorder
import numpy as np
from scipy.io.wavfile import write
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct
import json
import datetime

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """

    audio = audiorecorder(
        start_prompt="発話開始",
        pause_prompt="やり直す",
        stop_prompt="発話終了",
        start_style={"color":"white", "background-color":"black"},
        pause_style={"color":"gray", "background-color":"white"},
        stop_style={"color":"white", "background-color":"black"}
    )

    if len(audio) > 0:
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="en"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def transcribe_audio_japanese(audio_input_file_path):
    """
    日本語音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="ja"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    一旦mp3形式で音声ファイル作成後、wav形式に変換
    Args:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """

    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/temp_audio_output_{int(time.time())}.mp3"
    with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
        temp_audio_output_file.write(llm_response_audio)
    
    audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
    audio_mp3.export(audio_output_file_path, format="wav")

    # 音声出力用に一時的に作ったmp3ファイルを削除
    os.remove(temp_audio_output_filename)

def play_wav(audio_output_file_path, speed=1.0):
    """
    音声ファイルの読み上げ
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
    """

    # 音声ファイルの読み込み
    audio = AudioSegment.from_wav(audio_output_file_path)
    
    # 速度を変更
    if speed != 1.0:
        # frame_rateを変更することで速度を調整
        modified_audio = audio._spawn(
            audio.raw_data, 
            overrides={"frame_rate": int(audio.frame_rate * speed)}
        )
        # 元のframe_rateに戻すことで正常再生させる（ピッチを保持したまま速度だけ変更）
        modified_audio = modified_audio.set_frame_rate(audio.frame_rate)

        modified_audio.export(audio_output_file_path, format="wav")

    # PyAudioで再生
    with wave.open(audio_output_file_path, 'rb') as play_target_file:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(play_target_file.getsampwidth()),
            channels=play_target_file.getnchannels(),
            rate=play_target_file.getframerate(),
            output=True
        )

        data = play_target_file.readframes(1024)
        while data:
            stream.write(data)
            data = play_target_file.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()
    
    # LLMからの回答の音声ファイルを削除
    os.remove(audio_output_file_path)

def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = ConversationChain(
        llm=st.session_state.llm,
        memory=st.session_state.memory,
        prompt=prompt
    )

    return chain

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=problem
    )

    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio

def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation

def save_learned_phrase(phrase, category, context=""):
    """
    学習したフレーズを保存
    Args:
        phrase: 学習したフレーズ
        category: カテゴリ
        context: 使用場面や説明
    """
    if "learned_phrases" not in st.session_state:
        st.session_state.learned_phrases = []
    
    phrase_data = {
        "phrase": phrase,
        "category": category,
        "context": context,
        "learned_date": datetime.datetime.now().isoformat(),
        "practice_count": 0,
        "mastery_level": 0  # 0: 未習得, 1: 学習中, 2: 習得済み
    }
    
    st.session_state.learned_phrases.append(phrase_data)

def get_learned_phrases_by_category(category=None):
    """
    学習したフレーズを取得
    Args:
        category: カテゴリでフィルタリング（Noneの場合は全て）
    Returns:
        学習したフレーズのリスト
    """
    if "learned_phrases" not in st.session_state:
        return []
    
    if category:
        return [p for p in st.session_state.learned_phrases if p["category"] == category]
    return st.session_state.learned_phrases

def update_phrase_mastery(phrase, mastery_level):
    """
    フレーズの習得度を更新
    Args:
        phrase: 更新するフレーズ
        mastery_level: 習得度（0: 未習得, 1: 学習中, 2: 習得済み）
    """
    if "learned_phrases" not in st.session_state:
        return
    
    for p in st.session_state.learned_phrases:
        if p["phrase"] == phrase:
            p["mastery_level"] = mastery_level
            p["practice_count"] += 1
            break

def get_phrase_statistics():
    """
    フレーズ学習の統計情報を取得
    Returns:
        統計情報の辞書
    """
    if "learned_phrases" not in st.session_state:
        return {"total": 0, "by_category": {}, "mastery_levels": {"0": 0, "1": 0, "2": 0}}
    
    phrases = st.session_state.learned_phrases
    stats = {
        "total": len(phrases),
        "by_category": {},
        "mastery_levels": {"0": 0, "1": 0, "2": 0}
    }
    
    for phrase in phrases:
        # カテゴリ別集計
        category = phrase["category"]
        if category not in stats["by_category"]:
            stats["by_category"][category] = 0
        stats["by_category"][category] += 1
        
        # 習得度別集計
        mastery = str(phrase["mastery_level"])
        stats["mastery_levels"][mastery] += 1
    
    return stats

def create_reaction_practice_chain():
    """
    リアクション練習用のChain作成
    """
    return create_chain(ct.SYSTEM_TEMPLATE_REACTION_PRACTICE)

def create_phrase_learning_chain():
    """
    フレーズ学習用のChain作成
    """
    return create_chain(ct.SYSTEM_TEMPLATE_PHRASE_LEARNING)

def get_english_assistance(japanese_request):
    """
    日本語の要望から英語表現をアシスト
    Args:
        japanese_request: 日本語での要望
    Returns:
        英語表現の提案
    """
    assistance_prompt = f"""
    ユーザーが日本語で以下の要望を伝えました：
    「{japanese_request}」
    
    この要望を自然な英語で表現するためのフレーズを提案してください。
    以下の形式で回答してください：
    
    【基本表現】
    - 最も自然で一般的な表現
    
    【丁寧な表現】
    - より丁寧な言い方
    
    【カジュアルな表現】
    - 友達同士で使える表現
    
    【使用場面】
    - この表現を使う適切な場面
    
    【関連フレーズ】
    - 似たような意味の他の表現
    
    実用的で覚えやすい表現を心がけてください。
    """
    
    response = st.session_state.openai_obj.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": assistance_prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def save_assisted_phrase(english_phrase, japanese_request, context=""):
    """
    アシストされたフレーズを学習フレーズとして保存
    Args:
        english_phrase: 英語フレーズ
        japanese_request: 元の日本語要望
        context: 使用場面
    """
    if "learned_phrases" not in st.session_state:
        st.session_state.learned_phrases = []
    
    phrase_data = {
        "phrase": english_phrase,
        "category": "assisted",  # アシストされたフレーズ用のカテゴリ
        "context": f"日本語要望: {japanese_request} | {context}",
        "learned_date": datetime.datetime.now().isoformat(),
        "practice_count": 0,
        "mastery_level": 0
    }
    
    st.session_state.learned_phrases.append(phrase_data)