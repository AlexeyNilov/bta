# bta
Book to Audio converter

## Flow

```bash
pandoc input/book.epub -t markdown_strict -o input/book.md

bta convert input/book.md

for f in output/input_*.wav; do
    echo "file '$PWD/$f'"
done > output/inputs.txt
ffmpeg -f concat -safe 0 -i output/inputs.txt \
       -c:a libmp3lame -q:a 2 \
       output/final.mp3\

ffplay output/final.mp3
```

## Refernces

For PDF convertion see https://github.com/run-llama/liteparse
