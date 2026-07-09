from flask import Flask, request, jsonify
import base64
from io import BytesIO
from PIL import Image
import os
import pytesseract
from spellchecker import SpellChecker
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe" #путь к тессеракту
spell = SpellChecker(language='ru')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Доска</title>
  <style>
    body {font-family: Arial, sans-serif; padding: 10px; }
    canvas { border: 3px solid #000000; background: #c2c2c4; touch-action: none; cursor: crosshair ; }
    button { padding: 10px 20px; margin-right: 10px; marign-left: 15px; margin-top: 1px; cursor: pointer; }
    label{  margin-right: 15px;}
    textarea {resize: none; margin-top: 3px;}
    .text-output {
    height: 25px;         
    margin-top: 1px;
    font-size: 25px;
  }
  </style>
</head>
<body>
  <h2 align='center'>Доска</h2>
  <canvas id="canvas" width="1875" height="700" align='center'></canvas>

  <div class="controls">
    <label><input type="color" id="color" value="#000000"></label>
    <button id="clear">Очистить</button>
    <button id="pen" type="button">Карандаш</button>
    <button id="eraser" type="button">Ластик</button>
    <button id="send" type="button">Проверить</button>
    <button onclick="giveatask()">Задание</button>
    <button id="fsBtn">Полн. экран</button>
    
    <h3>Результат:</h3>

    <b>Распознанный текст:</b>
    <pre id="recognized" class="text-output"></pre>

    <b>Исправленный текст:</b>
    <pre id="corrected" class="text-output"></pre>
    <div class="task-line">
    <strong>Задание:</strong>
    <span id="randomTask"></span>
    </div>
  </div>


  <script>
    
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const colorPicker = document.getElementById('color');
    const items = [
    "Напиши правильно: мошина самалет зерколо рубажка ",
    "Напиши правильно: гозета галова кника повор сонце",
    "Напиши правильно: крук ромп  обpикoc баpьбa",
    "Напиши правильно: На новый год мне подарили падарок"
];
document.getElementById('pen').onclick = () => {
  ctx.globalCompositeOperation = 'source-over';
  ctx.lineWidth = 3;
};

document.getElementById('eraser').onclick = () => {
  ctx.globalCompositeOperation = 'destination-out';
  ctx.lineWidth = 20;
};

const btn = document.getElementById('fsBtn');
  btn.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen(); 
    } else {
      document.exitFullscreen(); 
    }
  });
function giveatask() {
    const randomIndex = Math.floor(Math.random() * items.length);
    document.getElementById("randomTask").innerText = items[randomIndex];
}
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    let drawing = false;
    function applyStyle() {
      ctx.strokeStyle = colorPicker.value;
    }
    applyStyle();
    colorPicker.addEventListener('change', applyStyle);

    function pos(evt) {
      const rect = canvas.getBoundingClientRect();
      return {
        x: (evt.clientX || evt.touches[0].clientX) - rect.left,
        y: (evt.clientY || evt.touches[0].clientY) - rect.top
      };
    }

    canvas.addEventListener('mousedown', e => { drawing = true; const p = pos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); });
    canvas.addEventListener('mousemove', e => { if (!drawing) return; const p = pos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); });
    canvas.addEventListener('mouseup', e => { drawing = false; });
    canvas.addEventListener('mouseout', e => { drawing = false; });

    document.getElementById('clear').onclick = () => { ctx.clearRect(0,0,canvas.width,canvas.height); };

    document.getElementById('send').onclick = async () => {
     const dataURL = canvas.toDataURL('image/png');

    const response = await fetch('/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: dataURL })
    });

    const data = await response.json();

    document.getElementById('recognized').textContent = data.recognized;
    document.getElementById('corrected').textContent = data.corrected;
};
  </script>
</body>
</html>
"""

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()             
    data_url = data['image']            
    encoded = data_url.split(',')[1]      
    image_bytes = base64.b64decode(encoded)  
    img = Image.open(BytesIO(image_bytes))                            #text - картинка = проблема
    img.save('text.png')                                              #corrected_text - проверенный и исправленый текст
    text = Image.open("text.png") 
    config = r'--psm 3'                                                 #textimage - картинка с текстом
    stext = pytesseract.image_to_string(text, lang='rus', config=config)    
    stext = stext.lower()                                              #stext - считаный текст                                 
    words = stext.split()                                              #words - все слова 
    misspelled = spell.unknown(words)                                 #misspelled - слова с ошибками 
    corrected_words = []      
    for wword in words:
      if wword in misspelled:
        corrected_words.append(spell.correction(wword))
      else:
        corrected_words.append(wword)
    corrected_text = " ".join(corrected_words)
    print('corrected_text:',corrected_text, 'stext;',stext,  'words;',words, 'misspelled;',misspelled)
    return jsonify({
    "recognized": stext,
    "corrected": corrected_text
    })
                    
                                                                                                                                      
if __name__ == '__main__':

    app.run(debug=True)