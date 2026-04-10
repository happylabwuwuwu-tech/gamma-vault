import streamlit as st
import streamlit.components.v1 as components

# 設定頁面語系與標題（Streamlit 層級）
st.set_page_config(page_title="GAMMA 雲端智慧照護平台", layout="wide")

# 將你的 HTML 代碼放入一個字串中
html_code = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>GAMMA 雲端智慧照護平台</title>
  
  <script src="https://cdn.tailwindcss.com"></script>
  
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>

  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f8fafc; color: #1e293b; padding-bottom: env(safe-area-inset-bottom); }
    /* ... 你的其他 CSS ... */
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    /* ... 你的 React 代碼 ... */
    const { useState, useEffect, useMemo } = React;
    // (此處省略你原本長長的 React 程式碼，請完整保留貼入)
    
    const App = () => {
        // ...
    };

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
"""

# 使用 Streamlit 渲染 HTML
# padding 為 0 讓它看起來像原生 App
st.components.v1.html(html_code, height=900, scrolling=True)
