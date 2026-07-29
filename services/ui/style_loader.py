import os
import streamlit as st
import streamlit.components.v1 as components
import base64
 

def load_css(file_path):
    if os.path.exists(file_path):
        st.markdown(
            """
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400&family=Inter:wght@400&display=swap" rel="stylesheet">
            """,
            unsafe_allow_html=True,
        )
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def inject_local_font(font_path, font_name):
    if not os.path.exists(font_path):
        return
    
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(font_path)[1].lstrip(".")
    fmt = {"otf": "opentype"}.get(ext, ext)
    mime = {"otf": "font/otf"}.get(ext, f"font/{ext}")

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url('data:{mime};base64,{encoded}') format('{fmt}');
            font-weight: 100 900;
            font-style: normal;
        }}
        </style>
    """, unsafe_allow_html=True)

def inject_webrtc_styles():
    font_path = os.path.join(os.getcwd(), "static", "AdobeClean.otf")
    
    if not os.path.exists(font_path):
        return

    with open(font_path, "rb") as font_file:
        encoded_font = base64.b64encode(font_file.read()).decode()

    components.html(
        f"""
        <script>
        (function patchWebRTCStyles() {{
            function injectIntoIframe(iframe) {{
                try {{
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || !doc.head) return;
                    if (doc.head.querySelector('#webrtc-custom-styles')) return;
                    const style = doc.createElement('style');
                    style.id = 'webrtc-custom-styles';
                    style.textContent = `
                        @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400&family=Inter:wght@400&display=swap');
                        .MuiButtonBase-root,
                        .MuiButton-root,
                        .MuiButton-contained,
                        .MuiButton-text {{
                            border-radius: 9999px !important;
                            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
                            letter-spacing: 0 !important;
                            border: 1px solid rgba(255, 255, 255, 0.25) !important;
                            background-color: transparent !important;
                            color: #ffffff !important;
                        }}
                    `;
                    doc.head.appendChild(style);
                }} catch (e) {{
                    console.warn('[patcher] could not inject:', e);
                }}
            }}

            function findAndPatch() {{
                const parentDoc = window.parent.document;
                const iframes = parentDoc.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    if (iframe.src && iframe.src.includes('webrtc')) {{
                        if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
                            injectIntoIframe(iframe);
                        }} else {{
                            iframe.addEventListener('load', () => injectIntoIframe(iframe));
                        }}
                    }}
                }});
            }}

            findAndPatch();
        }})();
        </script>
        """,
        height=0,
    )
