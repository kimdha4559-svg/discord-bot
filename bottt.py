import asyncio
import re
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# -------------------------------------------------------------
# 🔤 영타 -> 한글 변환 로직 (한영 오타/우회 자동 변환)
# -------------------------------------------------------------
CHO = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JOO = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

ENG_TO_KOR_MAP = {
    'q': 'ㅂ', 'Q': 'ㅃ', 'w': 'ㅈ', 'W': 'ㅉ', 'e': 'ㄷ', 'E': 'ㄸ', 'r': 'ㄱ', 'R': 'ㄲ', 't': 'ㅅ', 'T': 'ㅆ',
    'y': 'ㅛ', 'u': 'ㅕ', 'i': 'ㅑ', 'o': 'ㅐ', 'O': 'ㅒ', 'p': 'ㅔ', 'P': 'ㅖ', 'a': 'ㅁ', 's': 'ㄴ', 'd': 'ㅇ',
    'f': 'ㄹ', 'g': 'ㅎ', 'h': 'ㅗ', 'j': 'ㅓ', 'k': 'ㅏ', 'l': 'ㅣ', 'z': 'ㅋ', 'x': 'ㅌ', 'c': 'ㅊ', 'v': 'ㅍ',
    'b': 'ㅠ', 'n': 'ㅜ', 'm': 'ㅡ'
}

# 이중모음 및 복합자음 조합 매핑
DOUBLE_JOO = {('ㅗ', 'ㅏ'): 'ㅘ', ('ㅗ', 'ㅐ'): 'ㅙ', ('ㅗ', 'ㅣ'): 'ㅚ', ('ㅜ', 'ㅓ'): 'ㅝ', ('ㅜ', 'ㅔ'): 'ㅞ', ('ㅜ', 'ㅣ'): 'ㅟ', ('ㅡ', 'ㅣ'): 'ㅢ'}
DOUBLE_JONG = {('ㄱ', 'ㅅ'): 'ㄳ', ('ㄴ', 'ㅈ'): 'ㄵ', ('ㄴ', 'ㅎ'): 'ㄶ', ('ㄹ', 'ㄱ'): 'ㄺ', ('ㄹ', 'ㅁ'): 'ㄻ', ('ㄹ', 'ㅂ'): 'ㄼ', ('ㄹ', 'ㅅ'): 'ㄽ', ('ㄹ', 'ㅌ'): 'ㄾ', ('ㄹ', 'ㅍ'): 'ㄿ', ('ㄹ', 'ㅎ'): 'ㅀ', ('ㅂ', 'ㅅ'): 'ㅄ'}

def eng_to_kor(text):
    """ 영문 입력(qhwl, wkwl 등)을 한글(보지, 자지 등)로 변환해주는 함수 """
    # 1. 영문 자모 변환
    kor_jamo = [ENG_TO_KOR_MAP.get(ch, ch) for ch in text]
    
    # 변환할 한글 문자가 없으면 원래 텍스트 반환
    if not any(ch in CHO or ch in JOO for ch in kor_jamo):
        return text

    res = []
    i = 0
    n = len(kor_jamo)

    while i < n:
        # 초성 확인
        if kor_jamo[i] in CHO:
            c_idx = CHO.index(kor_jamo[i])
            i += 1
            # 중성 확인
            if i < n and kor_jamo[i] in JOO:
                v_char = kor_jamo[i]
                i += 1
                # 이중 모음 체크
                if i < n and (v_char, kor_jamo[i]) in DOUBLE_JOO:
                    v_char = DOUBLE_JOO[(v_char, kor_jamo[i])]
                    i += 1
                v_idx = JOO.index(v_char)

                # 종성 확인
                j_idx = 0
                if i < n and kor_jamo[i] in JONG and kor_jamo[i] != '':
                    # 뒤에 모음이 오면 다음 음절의 초성으로 넘김
                    if i + 1 < n and kor_jamo[i + 1] in JOO:
                        j_idx = 0
                    else:
                        j_char = kor_jamo[i]
                        # 복합 종성 체크
                        if i + 1 < n and (j_char, kor_jamo[i + 1]) in DOUBLE_JONG and not (i + 2 < n and kor_jamo[i + 2] in JOO):
                            j_char = DOUBLE_JONG[(j_char, kor_jamo[i + 1])]
                            i += 1
                        j_idx = JONG.index(j_char)
                        i += 1

                # 음절 완성
                syllable = chr(0xAC00 + (c_idx * 21 * 28) + (v_idx * 28) + j_idx)
                res.append(syllable)
            else:
                res.append(CHO[c_idx])
        else:
            res.append(kor_jamo[i])
            i += 1

    return "".join(res)

# -------------------------------------------------------------
# 🚨 1. 카테고리별 금지어 분류 딕셔너리
# -------------------------------------------------------------
BAD_WORDS = {
    "욕설": [
        "씨발", "시발", "개새끼", "병신", "지랄", "애미", "애비", "븅신", "ㅄ", "ㅂㅅ", 
        "ㅅㅂ", "ㅅ1ㅂ", "ㅂ1ㅅ", "ㅈㄹ", "개시발", "wtf", "ㄴㅇㅁ", "ㄴㅇㅂ", 
        "니애비", "니애미", "ㅆㅂ", "개병신", "븅", "븅딱", "개련", "개색", "tlqkf", 
        "🖕", "ㅗ", "니앰", "앰창", "m창", "엠창", "니앱", "애미없", "애비없"
    ],
    "일베용어": [
        "노무현", "mc무현", "일베", "응디시티", "이기야", "우흥", "운지", "북딱", 
        "이기", "응디", "흔들어라", "523", "노사모", "우파", "영태", "황영태", 
        "양숙", "운지라이더", "북", "딱", "짜장면", "부엉이바위", "코알라", 
        "노알라", "부엉이", "노짱", "피아제", "ㅂㄸㅎㄷㄹㄹ", "북딱흔드르라", 
        "노유찬", "따악좋다", "딱좋다", "성능좋다", "운지무현", "무현", "현무", 
        "일간베스트", "데일리베스트", "dailybest", "마파두부", "외상", "노무", "노무라이", 
        "문재인", "찢", "드럼통", "부엉이바위의진실", "2009", "0523", "20090523", "기분좋다", 
        "봉하", "봉하마을", "김해시", "언조비카이", "안된다..", "안된다", "밀어버려", 
        "미국한테", "매달려가지고", "미국", "형님형님", "형님야~", "바짓가랑이", "응딩이", 
        "별들달고", "별들 달고", "거들먹대고", "말았다는 얘깁니까", "기분좋다", "딱좋다", 
        "오늘은 제가 쏩니다", "쏩니다", "흔들", "바위", "작전통제권", "뺑뺑뻉뻉이", 
        "뺑뺑", "뻉뺑", "뻉뻉", "군대들", "지금까지 뭐했노", "뭐했노", "심심하면", 
        "불러다가", "부흥", "중력절", "중력", "사자바위", "내리막을", "6퍼센트", "7퍼센트", 
        "6%", "7%", "김대중", "문재인", "재인", "때리맥", "친북", "뇌물", "별들달고", 
        "양보없는", "꺼드럭", "MC", "오이삼", "찰과상", "자살골을", "일게이", "매끼나라", 
        "SWAG", "스웩", "직무유기", "성명", "자기들이", "국방장관", "참모총장", "경제", 
        "five two three", "자기들나라", "매끼나라", "확 올", "확 내", "올라갔다가", 
        "아주빠르게", "아주 빠르게", "말이나", "말놓고"
    ],
    "섹드립": [
        "보지", "자지", "섹스", "대딸", "따먹", "보빨", "딸", "섹", "폰섹", 
        "딸딸이", "ㅅㅅ", "핑보", "딜도"
    ]
}

user_chat_history = {}
channel_message_buffer = {}

def clean_text(text):
    """ 특수문자/숫자/공백 제거 함수 """
    text_lower = text.lower()
    cleaned = re.sub(r'[^가-힣a-zㄱ-ㅎㅏ-ㅣ]', '', text_lower)
    return cleaned

@bot.event
async def on_ready():
    print(f'성공적으로 로그인했습니다: {bot.user.name}')
    print('----------------------------------')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content
    lower_content = content.lower().replace(" ", "").strip()
    
    # 🔀 1) 영타 입력 시 한글로 자동 변환 (예: qhwl -> 보지, wkwl -> 자지)
    converted_kor = eng_to_kor(content)
    
    # 2) 원본 및 변환된 텍스트 정제 (특수문자/숫자/공백 제거)
    pure_text = clean_text(content)
    pure_converted = clean_text(converted_kor)

    detected_category = None

    # 3) 단일 메시지 검사 (영타 변환 텍스트 포함)
    for category, words in BAD_WORDS.items():
        for word in words:
            clean_word = word.lower().replace(" ", "")
            pure_word = clean_text(word)
            
            # 원본, 영타 변환글, 정제글 종합 대조
            if ((clean_word and (clean_word in lower_content or clean_word in converted_kor.lower())) or 
                (pure_word and (pure_word in pure_text or pure_word in pure_converted))):
                detected_category = category
                break
        if detected_category:
            break

    # 4) 끊어 보내기 버퍼 처리
    channel_id = message.channel.id
    if channel_id not in channel_message_buffer:
        channel_message_buffer[channel_id] = []

    # 버퍼에는 정제된 한글 변환 텍스트 저장 (영타로 끊어치는 경우도 방지)
    channel_message_buffer[channel_id].append(pure_converted if pure_converted else pure_text)
    if len(channel_message_buffer[channel_id]) > 10:
        channel_message_buffer[channel_id].pop(0)

    # 5) 최근 끊어 보내기 메시지 결합 검사
    if not detected_category:
        combined_text = "".join(channel_message_buffer[channel_id])
        
        for category, words in BAD_WORDS.items():
            for word in words:
                pure_word = clean_text(word)
                if pure_word and pure_word in combined_text:
                    detected_category = category
                    channel_message_buffer[channel_id] = []
                    break
            if detected_category:
                break

    # 6) 감지 시 발언 기록 및 맞춤형 경고 메시지 출력
    if detected_category:
        user_id = message.author.id
        
        if user_id not in user_chat_history:
            user_chat_history[user_id] = []

        # 발언 기록 저장
        user_chat_history[user_id].append({
            "category": detected_category,
            "content": content
        })

        # 카테고리별 맞춤 경고 멘트
        if detected_category == "욕설":
            warning_text = (
                f"{message.author.mention} 님, 욕설을 사용했다잭. 욕설은 나쁘다잭.\n"
                f"자꾸 욕설을 쓰면, 발딕이 웋~ 하고 밀어버린다잭."
            )
        elif detected_category == "일베용어":
            warning_text = (
                f"{message.author.mention} 님, 일베를 했다잭. 노무현이 불쌍하다잭.\n"
                f"노무현이 어떤사람인지는 알기나 하냐잭?\n"
                f"그거 힙한거 아니다잭. 친구들이 웃으니까 힙한줄아냐잭?\n"
                f"자꾸 일베하면 슈퍼잭이랑 등산간다잭~"
            )
        elif detected_category == "섹드립":
            warning_text = (
                f"{message.author.mention} 님, 자꾸 섹드립을 하면 어떡해잭\n"
                f"섹드립은 정말 나쁜거다잭.\n"
                f"섹드립하면 내가 너 찾아가서 실사판해주겠다잭.\n"
                f"교육사 대령 발딕이 너 잡아간다잭."
            )

        # 멘트 전송 (영구 보존)
        await message.channel.send(warning_text)

    await bot.process_commands(message)

# 7. 내역 확인 명령어
@bot.command(name='내역확인')
async def check_history(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    user_id = target.id

    if user_id not in user_chat_history or not user_chat_history[user_id]:
        await ctx.send(f"✅ {target.mention} 님은 기록된 부적절한 발언이 없습니다.")
        return

    history_list = user_chat_history[user_id]
    
    counts = {"욕설": 0, "일베용어": 0, "섹드립": 0}
    for item in history_list:
        counts[item["category"]] += 1

    embed = discord.Embed(
        title=f"📜 {target.display_name} 님의 부적절한 발언 모아보기",
        description=f"총 누적 위반 횟수: **{len(history_list)}회**\n• 욕설: {counts['욕설']}회 | • 일베: {counts['일베용어']}회 | • 섹드립: {counts['섹드립']}회",
        color=discord.Color.dark_red()
    )

    recent_logs = history_list[-10:]
    log_text = ""
    for idx, log in enumerate(recent_logs, 1):
        log_text += f"`{idx}. [{log['category']}]` {log['content']}\n"

    embed.add_field(name="최근 적발된 발언 목록 (최대 10개)", value=log_text if log_text else "기록 없음", inline=False)
    
    await ctx.send(embed=embed)

# 봇 실행
bot.run("MTU2MjQ0Njg1ODQ4NjU1MDUzOQ.GLE_3b.A2VIxKBwvjH_47gXl9Ec6C8EFNWfd53z5hFa9s")
