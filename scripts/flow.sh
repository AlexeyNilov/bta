book_name=test

for f in output/$book_name_*.wav; do
    echo "file '$PWD/$f'"
done > output/$book_name.txt
ffmpeg -f concat -safe 0 -i output/$book_name.txt \
       -c:a libmp3lame -q:a 2 \
       output/$book_name.mp3