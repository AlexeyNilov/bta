# bta
Book to Audio converter

## Flow

```bash
book_name=book
pandoc input/$book_name.epub -t markdown_strict -o input/$book_name.md

bta convert input/$book_name.md

for f in output/$book_name_*.wav; do
    echo "file '$PWD/$f'"
done > output/$book_name.txt
ffmpeg -f concat -safe 0 -i output/inputs.txt \
       -c:a libmp3lame -q:a 2 \
       output/$book_name.mp3\

ffplay output/$book_name.mp3
```

## Refernces

* For EPUB to text convertion: https://pandoc.org/
* For PDF to text convertion: https://github.com/run-llama/liteparse
* TTS: https://github.com/kyutai-labs/pocket-tts
