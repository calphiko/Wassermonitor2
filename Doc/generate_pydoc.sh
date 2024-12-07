
source ../.venv/bin/activate

cd ../Pi/
pydoc3 main.py
mv main.html ../Doc/content/10_Functions_Reference/pi.html

cd ../Server/API/

pydoc3 main.py
mv main.html ../../Doc/content/10_Functions_Reference/api.html

cd ../Warningbot/

pydoc3 main.py
mv main.html ../../Doc/content/10_Functions_Reference/warning_bot.html

cd ../../
