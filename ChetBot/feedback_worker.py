import discord
from discord.ext import tasks, commands
import sqlite3
import os

class FeedbackWorker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "../404_system.db" 
        self.notifier_loop.start()

    def cog_unload(self):
        self.notifier_loop.cancel()

    @tasks.loop(seconds=20)
    async def notifier_loop(self):
        if not os.path.exists(self.db_path):
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Читаем структуру таблицы
                cursor.execute("PRAGMA table_info(feedback_cases)")
                columns = [info[1] for info in cursor.fetchall()]
                
                id_col = "case_id" if "case_id" in columns else "id"
                user_col = "submitter_id" if "submitter_id" in columns else "user_id"
                
                # Ищем текстовую колонку без риска краша
                text_col = None
                for col in ["reason", "description", "message", "content", "text", "category"]:
                    if col in columns:
                        text_col = col
                        break

                # Формируем безопасный запрос
                if text_col:
                    query = f"SELECT {id_col}, {user_col}, status, {text_col} FROM feedback_cases WHERE status IN ('approved', 'denied')"
                else:
                    query = f"SELECT {id_col}, {user_col}, status FROM feedback_cases WHERE status IN ('approved', 'denied')"
                    
                cursor.execute(query)
                cases = cursor.fetchall()

                for row in cases:
                    if text_col:
                        case_id, user_id, status, content = row
                    else:
                        case_id, user_id, status = row
                        content = "Текст заявки скрыт (структура БД не содержит поля текста)."
                    
                    # Отправка фидбека
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        embed = discord.Embed(
                            title="SYSTEM NOTIFICATION // TICKET RESOLVED",
                            description=f"Ваш запрос `#{case_id}` был рассмотрен администрацией.",
                            color=0x57ab5a if status == "approved" else 0xda3633
                        )
                        embed.add_field(name="Исходный текст:", value=str(content)[:1000], inline=False)
                        embed.add_field(name="Вердикт:", value="✅ ОДОБРЕНО" if status == "approved" else "❌ ОТКЛОНЕНО", inline=False)
                        
                        await user.send(embed=embed)
                        print(f"[WORKER] Уведомление успешно доставлено пользователю {user_id}")
                    except Exception as e:
                        print(f"[WORKER_ERR] Ошибка доставки ЛС пользователю {user_id}: {e}")
                    
                    # Закрываем тикет в базе
                    cursor.execute(f"UPDATE feedback_cases SET status = 'closed' WHERE {id_col} = ?", (case_id,))
                
                conn.commit()
        except Exception as e:
            print(f"[WORKER_CRITICAL] Сбой БД: {e}")

    @notifier_loop.before_loop
    async def before_notifier(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(FeedbackWorker(bot))