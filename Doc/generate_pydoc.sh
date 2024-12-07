
source ../.venv/bin/activate

cd ../Pi/
pydoc -w main
mv main.html ../Doc/content/10_Functions_Reference/pi.html

cd ../Server/API/

pydoc -w main
mv main.html ../../Doc/content/10_Functions_Reference/api.html

cd ../Warningbot/

pydoc -w main
mv main.html ../../Doc/content/10_Functions_Reference/warning_bot.html

cd ../../
