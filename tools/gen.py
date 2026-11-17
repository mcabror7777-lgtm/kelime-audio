# Kelime ovoz generatori: manifest.json dagi matnlardan MP3 yaratadi va kelime-audio.zip qiladi
import asyncio, json, os, sys, zipfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
LOG = os.path.join(HERE, "log.txt")

try:
    import edge_tts
except ImportError:
    print("edge-tts o'rnatilmagan. start.bat ni ishga tushiring.")
    sys.exit(1)

man = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
todo = [m for m in man if not (os.path.exists(os.path.join(OUT, m[0])) and os.path.getsize(os.path.join(OUT, m[0])) > 500)]
total, done, errors = len(man), len(man) - len(todo), []
start = time.time()

async def one(sem, item):
    global done
    path, voice, text = item
    dst = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(text, voice).save(dst + ".part")
                if os.path.getsize(dst + ".part") < 500:
                    raise RuntimeError("bo'sh fayl")
                os.replace(dst + ".part", dst)
                break
            except Exception as e:
                if attempt == 3:
                    errors.append(f"{path}\t{e}")
                await asyncio.sleep(2 + attempt * 3)
    done += 1
    if done % 50 == 0 or done == total:
        el = time.time() - start
        print(f"  {done}/{total} tayyor  ({el/60:.1f} daqiqa)", flush=True)

async def main():
    sem = asyncio.Semaphore(6)
    await asyncio.gather(*(one(sem, m) for m in todo))

print(f"Jami {total} ta fayl, {len(todo)} tasi yaratiladi...")
asyncio.run(main())

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(errors))

if errors:
    print(f"\n{len(errors)} ta xato. start.bat ni qayta ishga tushiring (tayyorlari qayta qilinmaydi).")
    sys.exit(2)

print("\nZip qilinyapti...")
zp = os.path.join(HERE, "kelime-audio.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
    for m in man:
        z.write(os.path.join(OUT, m[0]), m[0])
print(f"TAYYOR: {zp}  ({os.path.getsize(zp)/1e6:.0f} MB)")
print("Endi Claude'ga \"tayyor\" deb yozing.")
