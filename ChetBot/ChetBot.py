import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
from datetime import datetime, timezone
import aiohttp

# ===================== КОНФИГУРАЦИЯ =====================
BOT_TOKEN = "MTQ5NDIwODM2MjMzMjgxNTQ2MQ.G_ucx7.PHQfE0TXJ5tQkNgYaftMI2XeI827ckJU1ShOn0"
BUTTON_WEBHOOK_URL = "https://discord.com/api/webhooks/1431232310820343931/mX6EUaaZM-94JO378rsN2DH6wlP4DMO0Sl4fS6nHdygxMSNzqEBw9kXZAh2X7ESmeVEn"

INVITE_LOG_CHANNEL_ID = 1349964094375067649
DM_LOG_CHANNEL_ID = 1371770798087471114
WELCOME_CHANNEL_ID = 1324239354574540872
ANNOUNCEMENTS_CHANNEL_ID = 1348853550502903879

ROLES_CHANNEL_ID = 1324239354222346339
RULES_CHANNEL_ID = 1324239354222346338
SEARCH_PLAYERS_CHANNEL_ID = 1324239354708754476

FEEDBACK_LOG_CHANNEL_ID = 1371770798087471114

DATA_FILE = "invites_stats.json"

CHANNEL_MENU = 1394903967519080591
CHANNEL_COMPLAINT_PLAY = 1394902833618354186
CHANNEL_COMPLAINT_ADM = 1394902931089653761
CHANNEL_SUGGESTIONS = 1394903069745217557
CHANNEL_APPLY_ADMIN = 1394902974605557913

ROLE_PLAYERS = 1324239354209632358
ROLE_ADMINS = 1391928023996960798

USER_REVIEW_1 = 1014050100940652636
USER_REVIEW_2 = 337654182095880205

# ===================== ДАННЫЕ =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data(payload: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)


data = load_data()
stats = data.setdefault("stats", {})
invite_history = data.setdefault("invite_history", {})
feedback_counters = data.setdefault("feedback_counters", {})
feedback_cases = data.setdefault("feedback_cases", {})


def update_file():
    data["stats"] = stats
    data["invite_history"] = invite_history
    data["feedback_counters"] = feedback_counters
    data["feedback_cases"] = feedback_cases
    save_data(data)


# ===================== КОНФИГ FEEDBACK =====================
FEEDBACK_CATEGORIES = {
    "players": {
        "title": "Жалоба на игрока",
        "button_label": "⠀Жалоба на игроков⠀",
        "button_style": discord.ButtonStyle.danger,
        "channel_id": CHANNEL_COMPLAINT_PLAY,
        "case_prefix": "PR",
        "case_title": "Жалоба на игрока",
        "thread_name": "player-report",
        "review_role_ids": [ROLE_PLAYERS],
        "review_user_ids": [],
        "approved_text": "Игрок наказан.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на игрока",
        "fields": [
            {"key": "offender", "label": "Ник / ID игрока", "style": discord.TextStyle.short, "required": True, "max_length": 120},
            {"key": "complaint", "label": "Суть жалобы", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "datetime", "label": "Дата и время ситуации", "style": discord.TextStyle.short, "required": False, "max_length": 120},
            {"key": "proof", "label": "Доказательства", "style": discord.TextStyle.paragraph, "required": False, "max_length": 1000},
        ],
        "mini_summary_key": "offender",
    },
    "admins": {
        "title": "Жалоба на администрацию",
        "button_label": "⠀Жалоба на администрацию⠀",
        "button_style": discord.ButtonStyle.danger,
        "channel_id": CHANNEL_COMPLAINT_ADM,
        "case_prefix": "AR",
        "case_title": "Жалоба на администрацию",
        "thread_name": "admin-report",
        "review_role_ids": [ROLE_ADMINS],
        "review_user_ids": [USER_REVIEW_1, USER_REVIEW_2],
        "approved_text": "Жалоба принята.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на администрацию",
        "fields": [
            {"key": "offender", "label": "Ник администратора", "style": discord.TextStyle.short, "required": True, "max_length": 120},
            {"key": "complaint", "label": "Суть жалобы", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "datetime", "label": "Дата и время ситуации", "style": discord.TextStyle.short, "required": False, "max_length": 120},
            {"key": "proof", "label": "Доказательства", "style": discord.TextStyle.paragraph, "required": False, "max_length": 1000},
        ],
        "mini_summary_key": "offender",
    },
    "candidate": {
        "title": "Кандидат в администрацию",
        "button_label": "⠀Заявление в команду Администрации⠀",
        "button_style": discord.ButtonStyle.success,
        "channel_id": CHANNEL_APPLY_ADMIN,
        "case_prefix": "CA",
        "case_title": "Заявление в администрацию",
        "thread_name": "admin-candidate",
        "review_role_ids": [ROLE_ADMINS],
        "review_user_ids": [USER_REVIEW_1, USER_REVIEW_2],
        "approved_text": "Ваша заявка одобрена и передана на дальнейшее рассмотрение.",
        "denied_text": "Заявка отклонена.",
        "modal_title": "Заявление в администрацию",
        "fields": [
            {"key": "name", "label": "Ваше имя / ник", "style": discord.TextStyle.short, "required": True, "max_length": 120},
            {"key": "age", "label": "Ваш возраст", "style": discord.TextStyle.short, "required": True, "max_length": 20},
            {"key": "experience", "label": "Ваш опыт", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "motivation", "label": "Почему именно вы", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "online", "label": "Ваш онлайн / активность", "style": discord.TextStyle.short, "required": False, "max_length": 120},
        ],
        "mini_summary_key": "name",
    },
    "improve": {
        "title": "Идея по улучшению",
        "button_label": "⠀Предложение по улучшению⠀",
        "button_style": discord.ButtonStyle.primary,
        "channel_id": CHANNEL_SUGGESTIONS,
        "case_prefix": "IM",
        "case_title": "Предложение по улучшению",
        "thread_name": "improve-idea",
        "review_role_ids": [],
        "review_user_ids": [USER_REVIEW_1, USER_REVIEW_2],
        "approved_text": "Ваше предложение принято к рассмотрению.",
        "denied_text": "Предложение отклонено.",
        "modal_title": "Предложение по улучшению",
        "fields": [
            {"key": "idea", "label": "Название идеи", "style": discord.TextStyle.short, "required": True, "max_length": 120},
            {"key": "description", "label": "Описание идеи", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "benefit", "label": "Что это улучшит", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
            {"key": "implementation", "label": "Как это можно реализовать", "style": discord.TextStyle.paragraph, "required": False, "max_length": 1000},
        ],
        "mini_summary_key": "idea",
    },
}


# ===================== BOT =====================
intents = discord.Intents.default()
intents.members = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)
cached_invites: dict[int, list[discord.Invite]] = {}


# ===================== ХЕЛПЕРЫ =====================
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_case_counter(prefix: str) -> int:
    return int(feedback_counters.get(prefix, 0))


def next_case_id(prefix: str) -> str:
    current = get_case_counter(prefix) + 1
    feedback_counters[prefix] = current
    update_file()
    return f"{prefix}-{current:04d}"


def make_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📝 Обратная связь и обращения",
        description=(
            "Через панель ниже можно подать жалобу, предложение или заявку.\n"
            "Каждое обращение регистрируется и передаётся ответственным лицам.\n"
            "Ложные, спамные или заведомо недостоверные обращения могут повлечь санкции."
        ),
        color=discord.Color.from_rgb(43, 45, 49),
        timestamp=utcnow(),
    )
    embed.add_field(
        name="Что дальше",
        value=(
            "После отправки создаётся внутреннее обращение для проверки.\n"
            "Итог рассмотрения бот пришлёт вам в личные сообщения с номером обращения."
        ),
        inline=False,
    )
    embed.set_footer(text="Все обращения рассматриваются в порядке очереди")
    return embed


async def send_feedback_log(title: str, description: str, color: discord.Color = discord.Color.blurple()):
    ch = bot.get_channel(FEEDBACK_LOG_CHANNEL_ID)
    if not ch:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=utcnow(),
    )
    await ch.send(embed=embed)


def build_mentions(config: dict) -> str:
    parts = [f"<@&{role_id}>" for role_id in config["review_role_ids"]]
    parts.extend(f"<@{user_id}>" for user_id in config["review_user_ids"])
    return " ".join(parts).strip() or "Без упоминаний"


def upsert_embed_field(embed: discord.Embed, field_name: str, value: str, inline: bool = False):
    for index, field in enumerate(embed.fields):
        if field.name == field_name:
            embed.set_field_at(index, name=field_name, value=value, inline=inline)
            return
    embed.add_field(name=field_name, value=value, inline=inline)


async def add_reviewers_to_private_thread(thread: discord.Thread, guild: discord.Guild, config: dict):
    added_ids = set()

    for role_id in config["review_role_ids"]:
        role = guild.get_role(role_id)
        if not role:
            continue
        for member in role.members:
            if member.bot:
                continue
            if member.id in added_ids:
                continue
            try:
                await thread.add_user(member)
                added_ids.add(member.id)
            except (discord.Forbidden, discord.HTTPException):
                continue

    for user_id in config["review_user_ids"]:
        member = guild.get_member(user_id)
        if not member or member.bot or member.id in added_ids:
            continue
        try:
            await thread.add_user(member)
            added_ids.add(member.id)
        except (discord.Forbidden, discord.HTTPException):
            continue


def build_mini_embed(case_id: str, category_key: str, submitter: discord.Member, answers: dict) -> discord.Embed:
    config = FEEDBACK_CATEGORIES[category_key]
    summary_key = config["mini_summary_key"]
    summary_value = answers.get(summary_key, "—")

    embed = discord.Embed(
        title=f"📨 {config['case_title']} · {case_id}",
        color=discord.Color.blurple(),
        timestamp=utcnow(),
    )
    embed.add_field(name="Отправитель", value=submitter.mention, inline=True)
    embed.add_field(name="Тип", value=config["title"], inline=True)
    embed.add_field(name="Статус", value="На рассмотрении", inline=True)
    embed.add_field(name="Кратко", value=summary_value[:1024], inline=False)
    embed.set_footer(text=f"ID пользователя: {submitter.id}")
    return embed


def build_full_embed(case_id: str, category_key: str, submitter: discord.Member, answers: dict, public_message: discord.Message) -> discord.Embed:
    config = FEEDBACK_CATEGORIES[category_key]

    embed = discord.Embed(
        title=f"🔒 Внутреннее обращение · {case_id}",
        description=f"Категория: **{config['title']}**",
        color=discord.Color.orange(),
        timestamp=utcnow(),
    )
    embed.add_field(name="Отправитель", value=f"{submitter.mention} (`{submitter.id}`)", inline=False)
    embed.add_field(name="Публичное сообщение", value=f"[Открыть]({public_message.jump_url})", inline=False)

    for field in config["fields"]:
        label = field["label"]
        value = answers.get(field["key"], "—")
        embed.add_field(name=label, value=value[:1024] if value else "—", inline=False)

    embed.add_field(name="Статус", value="Ожидает решения", inline=False)
    embed.set_footer(text="Доступно только для staff")
    return embed


def build_decision_embed(case_id: str, category_key: str, status_text: str, reviewer: discord.Member) -> discord.Embed:
    config = FEEDBACK_CATEGORIES[category_key]
    color = discord.Color.green() if status_text == "Принято" else discord.Color.red()

    embed = discord.Embed(
        title=f"Решение по обращению {case_id}",
        description=f"Категория: **{config['title']}**",
        color=color,
        timestamp=utcnow(),
    )
    embed.add_field(name="Статус", value=status_text, inline=False)
    embed.add_field(name="Рассмотрел", value=f"{reviewer.mention} (`{reviewer.id}`)", inline=False)
    return embed


def build_user_dm(case_id: str, category_key: str, approved: bool, reviewer: discord.Member) -> discord.Embed:
    config = FEEDBACK_CATEGORIES[category_key]
    result_text = config["approved_text"] if approved else config["denied_text"]

    embed = discord.Embed(
        title=f"Результат по обращению №{case_id}",
        description="Ваше обращение было рассмотрено.",
        color=discord.Color.green() if approved else discord.Color.red(),
        timestamp=utcnow(),
    )
    embed.add_field(name="Категория", value=config["title"], inline=False)
    embed.add_field(name="Статус", value="Рассмотрено", inline=False)
    embed.add_field(name="Итог", value=result_text, inline=False)
    embed.add_field(name="Рассмотрел", value=f"{reviewer.mention} (`{reviewer.id}`)", inline=False)
    embed.set_footer(text=f"Номер обращения: {case_id}")
    return embed


async def disable_view_on_message(message: discord.Message, case_id: str, submitter_id: int, category_key: str):
    try:
        await message.edit(view=FeedbackDecisionView(case_id, submitter_id, category_key, disabled=True))
    except (discord.Forbidden, discord.HTTPException):
        pass


async def update_case_messages(case_data: dict, case_id: str, category_key: str, reviewer: discord.Member, approved: bool):
    status_value = f"Рассмотрено · {'Принято' if approved else 'Отклонено'}"
    color = discord.Color.green() if approved else discord.Color.red()

    public_channel = bot.get_channel(case_data.get("public_channel_id"))
    if isinstance(public_channel, discord.TextChannel):
        try:
            public_message = await public_channel.fetch_message(case_data["public_message_id"])
            if public_message.embeds:
                embed = public_message.embeds[0].copy()
                embed.color = color
                upsert_embed_field(embed, "Статус", status_value, inline=True)
                upsert_embed_field(embed, "Рассмотрел", f"{reviewer.mention}", inline=False)
                await public_message.edit(embed=embed)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    thread = bot.get_channel(case_data.get("thread_id"))
    if isinstance(thread, discord.Thread):
        try:
            decision_message = await thread.fetch_message(case_data["decision_message_id"])
            if decision_message.embeds:
                embed = decision_message.embeds[0].copy()
                embed.color = color
                upsert_embed_field(embed, "Статус", status_value, inline=False)
                upsert_embed_field(embed, "Рассмотрел", f"{reviewer.mention} (`{reviewer.id}`)", inline=False)
                await decision_message.edit(
                    embed=embed,
                    view=FeedbackDecisionView(case_id, case_data["submitter_id"], category_key, disabled=True),
                )
            else:
                await disable_view_on_message(decision_message, case_id, case_data["submitter_id"], category_key)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass


async def close_case(
    interaction: discord.Interaction,
    case_id: str,
    approved: bool,
):
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    case_data = feedback_cases.get(case_id)
    if not case_data:
        await interaction.followup.send("Не удалось найти данные обращения.", ephemeral=True)
        return

    if case_data.get("status") != "pending":
        await interaction.followup.send("По этому обращению уже принято решение.", ephemeral=True)
        return

    category_key = case_data["category_key"]
    status_text = "Принято" if approved else "Отклонено"
    reviewed_status = f"Рассмотрено · {status_text}"

    case_data["status"] = "approved" if approved else "denied"
    case_data["status_label"] = reviewed_status
    case_data["reviewed_by"] = interaction.user.id
    case_data["reviewed_at"] = utcnow().isoformat()
    update_file()

    await update_case_messages(case_data, case_id, category_key, interaction.user, approved)

    dm_ok = False
    user = interaction.guild.get_member(case_data["submitter_id"]) if interaction.guild else None
    if user is None:
        try:
            user = await bot.fetch_user(case_data["submitter_id"])
        except (discord.NotFound, discord.HTTPException):
            user = None

    if user is not None:
        try:
            await user.send(embed=build_user_dm(case_id, category_key, approved, interaction.user))
            dm_ok = True
        except (discord.Forbidden, discord.HTTPException):
            dm_ok = False

    await send_feedback_log(
        title="📌 Решение по обращению",
        description=(
            f"**Номер:** `{case_id}`\n"
            f"**Категория:** {FEEDBACK_CATEGORIES[category_key]['title']}\n"
            f"**Статус:** Рассмотрено\n"
            f"**Решение:** {status_text}\n"
            f"**Рассмотрел:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**DM:** {'Успешно' if dm_ok else 'Не удалось отправить'}"
        ),
        color=discord.Color.green() if approved else discord.Color.red(),
    )

    thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
    if thread:
        try:
            await thread.send(embed=build_decision_embed(case_id, category_key, status_text, interaction.user))
        except Exception as e:
            print(f"[THREAD SEND ERROR] {e}")

        try:
            await thread.edit(archived=True, locked=True)
            print(f"[THREAD CLOSED] {thread.id} -> archived=True locked=True")
        except Exception as e:
            print(f"[THREAD CLOSE ERROR] {e}")


async def create_feedback_case(interaction: discord.Interaction, category_key: str, answers: dict):
    config = FEEDBACK_CATEGORIES[category_key]

    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    parent_channel = bot.get_channel(config["channel_id"])

    if not isinstance(parent_channel, discord.TextChannel):
        await interaction.followup.send("Целевой канал не найден или не является текстовым.", ephemeral=True)
        return

    case_id = next_case_id(config["case_prefix"])

    mini_embed = build_mini_embed(case_id, category_key, interaction.user, answers)
    public_message = await parent_channel.send(embed=mini_embed)

    thread = await parent_channel.create_thread(
        name=f"{config['thread_name']}-{case_id.lower()}",
        type=discord.ChannelType.private_thread,
        invitable=False,
        auto_archive_duration=1440,
        reason=f"Внутреннее обращение {case_id}",
    )

    await add_reviewers_to_private_thread(thread, interaction.guild, config)

    mentions = build_mentions(config)
    try:
        await thread.send(
            content=mentions,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )
    except (discord.Forbidden, discord.HTTPException):
        pass

    full_embed = build_full_embed(case_id, category_key, interaction.user, answers, public_message)
    decision_view = FeedbackDecisionView(case_id, interaction.user.id, category_key)
    decision_message = await thread.send(embed=full_embed, view=decision_view)

    feedback_cases[case_id] = {
        "case_id": case_id,
        "category_key": category_key,
        "submitter_id": interaction.user.id,
        "public_channel_id": parent_channel.id,
        "public_message_id": public_message.id,
        "thread_id": thread.id,
        "decision_message_id": decision_message.id,
        "status": "pending",
        "created_at": utcnow().isoformat(),
    }
    update_file()

    await send_feedback_log(
        title="📥 Создано новое обращение",
        description=(
            f"**Номер:** `{case_id}`\n"
            f"**Категория:** {config['title']}\n"
            f"**Отправитель:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**Канал:** <#{parent_channel.id}>\n"
            f"**Ветка:** <#{thread.id}>\n"
            f"**Пинги:** {mentions}"
        ),
        color=discord.Color.blurple(),
    )

    await interaction.followup.send(
        f"Обращение зарегистрировано. Номер: **{case_id}**.\n"
        "Итог рассмотрения придёт вам в личные сообщения.",
        ephemeral=True,
    )


async def restore_feedback_views():
    for case_id, case_data in feedback_cases.items():
        if case_data.get("status") != "pending":
            continue
        message_id = case_data.get("decision_message_id")
        submitter_id = case_data.get("submitter_id")
        category_key = case_data.get("category_key")
        if not message_id or not submitter_id or not category_key:
            continue
        bot.add_view(FeedbackDecisionView(case_id, submitter_id, category_key), message_id=message_id)


# ===================== PERSISTENT VIEWS =====================
class FeedbackDecisionView(discord.ui.View):
    def __init__(self, case_id: str, submitter_id: int, category_key: str, disabled: bool = False):
        super().__init__(timeout=None)
        self.case_id = case_id
        self.submitter_id = submitter_id
        self.category_key = category_key

        approve_btn = discord.ui.Button(
            label="Принять",
            style=discord.ButtonStyle.success,
            custom_id=f"feedback_accept:{case_id}",
            disabled=disabled,
        )
        reject_btn = discord.ui.Button(
            label="Отклонить",
            style=discord.ButtonStyle.danger,
            custom_id=f"feedback_reject:{case_id}",
            disabled=disabled,
        )

        approve_btn.callback = self.approve_callback
        reject_btn.callback = self.reject_callback

        self.add_item(approve_btn)
        self.add_item(reject_btn)

    async def approve_callback(self, interaction: discord.Interaction):
        await close_case(interaction, self.case_id, approved=True)

    async def reject_callback(self, interaction: discord.Interaction):
        await close_case(interaction, self.case_id, approved=False)


class FeedbackModal(discord.ui.Modal):
    def __init__(self, category_key: str):
        self.category_key = category_key
        config = FEEDBACK_CATEGORIES[category_key]
        super().__init__(title=config["modal_title"], timeout=None)

        self.field_keys = []
        for field in config["fields"]:
            input_item = discord.ui.TextInput(
                label=field["label"],
                style=field["style"],
                required=field["required"],
                max_length=field["max_length"],
            )
            self.add_item(input_item)
            self.field_keys.append(field["key"])

    async def on_submit(self, interaction: discord.Interaction):
        answers = {}
        for key, child in zip(self.field_keys, self.children):
            if isinstance(child, discord.ui.TextInput):
                answers[key] = (child.value or "").strip() or "—"

        try:
            await create_feedback_case(interaction, self.category_key, answers)
        except Exception as exc:
            await send_feedback_log(
                title="❌ Ошибка при создании обращения",
                description=(
                    f"**Категория:** {FEEDBACK_CATEGORIES[self.category_key]['title']}\n"
                    f"**Пользователь:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Ошибка:** `{exc}`"
                ),
                color=discord.Color.red(),
            )
            if interaction.response.is_done():
                await interaction.followup.send("Не удалось создать обращение.", ephemeral=True)
            else:
                await interaction.response.send_message("Не удалось создать обращение.", ephemeral=True)


class FeedbackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for idx, (category_key, config) in enumerate(FEEDBACK_CATEGORIES.items()):
            button = discord.ui.Button(
                label=config["button_label"],
                style=config["button_style"],
                custom_id=f"feedback_open:{category_key}",
                row=idx,
            )

            async def callback(interaction: discord.Interaction, ck=category_key):
                await interaction.response.send_modal(FeedbackModal(ck))

            button.callback = callback
            self.add_item(button)


# ===================== EVENTS =====================
@bot.event
async def on_ready():
    if not getattr(bot, "_persistent_views_loaded", False):
        bot.add_view(FeedbackView())
        await restore_feedback_views()
        bot._persistent_views_loaded = True

    for guild in bot.guilds:
        try:
            cached_invites[guild.id] = await guild.invites()
        except discord.Forbidden:
            cached_invites[guild.id] = []

    await bot.load_extension("feedback_worker")
    await bot.tree.sync()
    print(f"{bot.user} запущен и готов к работе!")


@bot.event
async def on_invite_create(invite: discord.Invite):
    cached_invites.setdefault(invite.guild.id, []).append(invite)


@bot.event
async def on_invite_delete(invite: discord.Invite):
    cached_invites[invite.guild.id] = [
        item for item in cached_invites.get(invite.guild.id, []) if item.code != invite.code
    ]


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    try:
        new_invites = await guild.invites()
    except discord.Forbidden:
        new_invites = []

    old_invites = cached_invites.get(guild.id, [])
    used = None
    for new_inv in new_invites:
        for old_inv in old_invites:
            if new_inv.code == old_inv.code and new_inv.uses > old_inv.uses:
                used = new_inv
                break
        if used:
            break
    cached_invites[guild.id] = new_invites

    welcome_ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        await welcome_ch.send(
            f"Приветствую тебя {member.mention} на сервере **{guild.name}**! Теперь нас {guild.member_count}!"
        )

    if used and used.inviter:
        inviter_id = str(used.inviter.id)
        stats.setdefault(inviter_id, {"joins": 0, "leaves": 0, "invites": 0})
        stats[inviter_id]["joins"] += 1
        stats[inviter_id]["invites"] += 1
        invite_history[str(member.id)] = inviter_id
        update_file()

        embed_inv = discord.Embed(
            title="📥 Invite Log",
            description=(
                f"{used.inviter.mention} пригласил {member.mention}\n"
                f"Код: `{used.code}` | Всего приглашено: **{stats[inviter_id]['invites']}**"
            ),
            color=discord.Color.blurple(),
            timestamp=utcnow(),
        )
        ch = bot.get_channel(INVITE_LOG_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed_inv)

    dm_embed = discord.Embed(
        title="Добро пожаловать на Server 404: Server Not Found",
        description="Рады видеть тебя в нашем пространстве! Ниже — краткое руководство по ключевым ресурсам:",
        color=discord.Color.dark_blue(),
        timestamp=utcnow(),
    )
    dm_embed.set_thumbnail(url="https://i.imgur.com/4ydti00.png")

    dm_embed.add_field(
        name="〘❗〙 Объявления",
        value=f"<#{ANNOUNCEMENTS_CHANNEL_ID}> — все важные новости и анонсы",
        inline=False,
    )
    dm_embed.add_field(
        name="〘📜〙 Правила",
        value=f"<#{RULES_CHANNEL_ID}> — ознакомься перед общением",
        inline=False,
    )
    dm_embed.add_field(
        name="〘❗〙 Роли",
        value=f"<#{ROLES_CHANNEL_ID}> — получи доступ к привилегиям",
        inline=False,
    )
    dm_embed.add_field(
        name="〘🔎〙 Поиск игроков",
        value=f"<#{SEARCH_PLAYERS_CHANNEL_ID}> — найдёшь тиммейтов под свои задачи",
        inline=False,
    )
    dm_embed.add_field(
        name="📈 Система уровней",
        value=(
            "Наращивай активность в голосовых чатах и зарабатывай опыт — "
            "твоя роль и цвет ника будут расти вместе с тобой."
        ),
        inline=False,
    )
    dm_embed.add_field(
        name="💡 Советы по вливанию",
        value=(
            "1. Представься в чате.\n"
            "2. Загляни в раздел «Правила» и ставь реакцию ✔️.\n"
            "3. Выбери роли, которые тебе интересны.\n"
            "4. Не стесняйся задавать вопросы — мы тут все на «ты» :)"
        ),
        inline=False,
    )
    dm_embed.set_footer(text="Для помощи — обращайся к Администрации. По вопросам ботов — пиши Nanda070.")

    dm_sent = False
    try:
        await member.send(embed=dm_embed)
        dm_sent = True
    except discord.Forbidden:
        dm_sent = False

    dm_log = discord.Embed(
        title="📩 DM Log",
        color=discord.Color.green() if dm_sent else discord.Color.red(),
        timestamp=utcnow(),
    )
    dm_log.add_field(name="Пользователь", value=member.mention, inline=False)
    dm_log.add_field(name="Статус", value="✅ Отправлено" if dm_sent else "❌ Отказано", inline=False)

    dm_ch = bot.get_channel(DM_LOG_CHANNEL_ID)
    if dm_ch:
        await dm_ch.send(embed=dm_log)


@bot.event
async def on_member_remove(member: discord.Member):
    mid = str(member.id)
    if mid in invite_history:
        inv_id = invite_history.pop(mid)
        if inv_id in stats:
            stats[inv_id]["leaves"] += 1
        update_file()


# ===================== FEEDBACK COMMAND =====================
feedback_panel_group = app_commands.Group(
    name="feedback_panel",
    description="Управление панелью обратной связи",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


@feedback_panel_group.command(name="send", description="Опубликовать панель обратной связи")
@app_commands.describe(channel="Канал для публикации панели")
async def feedback_panel_send(
    interaction: discord.Interaction,
    channel: discord.TextChannel | None = None,
):
    target_channel = channel or interaction.channel

    if not isinstance(target_channel, discord.TextChannel):
        await interaction.response.send_message("Нужен обычный текстовый канал.", ephemeral=True)
        return

    message = await target_channel.send(embed=make_panel_embed(), view=FeedbackView())

    await send_feedback_log(
        title="🧩 Панель feedback опубликована",
        description=(
            f"**Кто:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**Канал:** {target_channel.mention}\n"
            f"**Сообщение:** [Открыть]({message.jump_url})"
        ),
        color=discord.Color.blurple(),
    )
    await interaction.response.send_message("Панель опубликована.", ephemeral=True)


bot.tree.add_command(feedback_panel_group)


# ===================== /button_create НЕ ТРОГАЕМ =====================
class DynamicQuestionsModal(discord.ui.Modal):
    def __init__(self, title: str, questions: list[str], button_name: str):
        super().__init__(title=title, timeout=None)
        self.questions = questions
        self.button_name = button_name
        self.inputs: list[discord.ui.TextInput] = []

        for idx, q in enumerate(self.questions, start=1):
            inp = discord.ui.TextInput(
                label=q[:45] if q else f"Вопрос {idx}",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000,
                placeholder="Ваш ответ…",
            )
            self.add_item(inp)
            self.inputs.append(inp)

    async def on_submit(self, interaction: discord.Interaction):
        answers = []
        for i, (q, inp) in enumerate(zip(self.questions, self.inputs), start=1):
            val = (inp.value or "").strip()
            answers.append((q or f"Вопрос {i}", val if val else "—"))

        embed = discord.Embed(
            title=f"📝 Ответ по кнопке: {self.button_name}",
            color=discord.Color.blurple(),
            timestamp=utcnow(),
        )
        embed.add_field(name="Отправитель", value=f"{interaction.user.mention}", inline=False)
        for q, a in answers:
            embed.add_field(name=q[:256] if q else "Вопрос", value=a[:1024] if a else "—", inline=False)
        embed.set_footer(text="404 Helper · Button Form")

        if not BUTTON_WEBHOOK_URL:
            await interaction.response.send_message(
                "BUTTON_WEBHOOK_URL не задан в переменных окружения.",
                ephemeral=True,
            )
            return

        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(BUTTON_WEBHOOK_URL, session=session)
                await webhook.send(
                    embed=embed,
                    username="404 Button Collector",
                    avatar_url="https://i.imgur.com/4ydti00.png",
                )
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ Ошибка отправки в вебхук: {exc}", ephemeral=True)
            return

        await interaction.response.send_message("✅ Отправлено!", ephemeral=True)


class DynamicButtonView(discord.ui.View):
    def __init__(self, button_name: str, questions: list[str]):
        super().__init__(timeout=None)
        self.button_name = button_name
        self.questions = [q for q in questions if q] or ["Ответ"]

        btn = discord.ui.Button(
            label=self.button_name[:80],
            style=discord.ButtonStyle.primary,
            custom_id=f"btn_form_{int(time.time())}",
        )

        async def on_click(interaction: discord.Interaction):
            modal = DynamicQuestionsModal(
                title=f"Форма: {self.button_name}",
                questions=self.questions,
                button_name=self.button_name,
            )
            await interaction.response.send_modal(modal)

        btn.callback = on_click
        self.add_item(btn)


@bot.tree.command(name="button_create", description="Создать кнопку, открывающую форму с вопросами (до 5 шт.)")
@app_commands.describe(
    name="Текст на кнопке",
    q1="Вопрос 1 (опционально)",
    q2="Вопрос 2 (опционально)",
    q3="Вопрос 3 (опционально)",
    q4="Вопрос 4 (опционально)",
    q5="Вопрос 5 (опционально)",
)
async def button_create(
    interaction: discord.Interaction,
    name: str,
    q1: str | None = None,
    q2: str | None = None,
    q3: str | None = None,
    q4: str | None = None,
    q5: str | None = None,
):
    questions = [q1, q2, q3, q4, q5]
    view = DynamicButtonView(button_name=name, questions=questions)
    await interaction.response.send_message(view=view)


# ===================== RUN =====================
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана.")
    bot.run(BOT_TOKEN)
