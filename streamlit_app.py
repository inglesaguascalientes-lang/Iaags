from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

try:
    import torch
    from transformers import pipeline
except Exception:  # pragma: no cover - handled at runtime
    torch = None
    pipeline = None

st.set_page_config(page_title="EcoAudit Aguascalientes", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8f4f1 0%, #ffffff 100%);
        color: #111111;
        font-size: 17px;
    }
    .stSidebar {
        background-color: #7a0f1a;
        color: #ffffff;
        font-size: 18px;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar p, .stSidebar div {
        color: #ffffff;
        font-size: 18px;
        line-height: 1.4;
    }
    .stSidebar .st-bq, .stSidebar .st-emotion-cache-1v0mbdj, .stSidebar .st-emotion-cache-1y4p8pa {
        color: #ffffff;
    }
    .report-card {
        background-color: #ffffff;
        color: #111111;
        padding: 24px;
        border-radius: 14px;
        border: 2px solid #7a0f1a;
        box-shadow: 0 4px 16px rgba(0,0,0,0.14);
        font-size: 17px;
        line-height: 1.6;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #7a0f1a;
    }
    .stButton>button {
        background-color: #7a0f1a;
        color: white;
        border: 1px solid #7a0f1a;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #5b0913;
        color: white;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #111111;
        border: 1px solid #7a0f1a;
    }
    .stCheckbox label {
        color: #111111;
        font-size: 16px;
        line-height: 1.4;
    }
    .stTextArea>div>div>textarea {
        min-height: 110px;
    }
    .st-bd, .st-emotion-cache-1xw8m1y {
        padding-top: 6px;
        padding-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("IAAGS.com")
    st.info("Herramienta de apoyo ambiental")
    st.divider()
    st.warning("Use este flujo para registrar observaciones de campo y generar una nota de apoyo para revisión interna.")

st.title("IAAGS.com")
st.write("Inteligencia Ambiental, Crecimiento Empresarial")
st.caption("Para fines de entretenimiento y demostración. No es una inspección formal ni una evaluación oficial.")


def get_risk_level(score: int) -> str:
    if score >= 70:
        return "ROJO / RED"
    if score >= 35:
        return "AMARILLO / YELLOW"
    return "VERDE / GREEN"


def get_violations(checks: dict) -> list[str]:
    violations = []
    if not checks["containment"]:
        violations.append("No se detectó contención secundaria ni charola de derrames")
    if checks["spills"]:
        violations.append("Se observaron derrames, manchas o fugas")
    if not checks["labels"]:
        violations.append("Faltan etiquetas visibles o identificación del riesgo")
    if not checks["cretib"]:
        violations.append("Falta el código CRETIB")
    if not checks["date"]:
        violations.append("Falta la fecha de generación")
    if not checks["docs"]:
        violations.append("Falta manifiesto, acuse o documentación oficial")
    if not checks["roof"]:
        violations.append("No se observa techo o almacenamiento protegido")
    if not checks["segregation"]:
        violations.append("No se evidencia segregación de residuos")
    if not checks["nra"]:
        violations.append("No se observa número NRA")
    if not checks["stamp"]:
        violations.append("No se observa sello oficial SEMARNAT / Acuse")
    if not checks["shelter"]:
        violations.append("No se observa protección contra intemperie o techo adecuado")
    if not checks["inventory"]:
        violations.append("No se evidencia inventario o control de residuos")
    if not checks["container"]:
        violations.append("No se observa integridad del contenedor o estado adecuado para transporte")
    if not checks["transfer"]:
        violations.append("No se evidencia control de transferencia o cadena de custodia")
    if not checks["destination"]:
        violations.append("No se evidencia destino final o ruta de disposición documentada")
    if not checks["hazard_id"]:
        violations.append("No se identifica claramente el tipo de residuo o riesgo presente")
    if not checks["spill_kit"]:
        violations.append("No se observa equipo o procedimiento para respuesta ante derrames")
    if not checks["closed_container"]:
        violations.append("El contenedor no parece cerrado, protegido o en condición de manejo seguro")
    if not checks["transport_control"]:
        violations.append("No se observa control claro del traslado o ruta de transporte")
    if not checks["disposal_evidence"]:
        violations.append("No se evidencia disposición final o seguimiento documental del residuo")
    return violations


def get_laws(checks: dict) -> list[str]:
    laws = []
    if not checks["containment"] or checks["spills"]:
        laws.append("LGPGIR - almacenamiento adecuado y prevención de derrames")
    if not checks["labels"] or not checks["cretib"]:
        laws.append("NOM-052 - etiquetado e identificación de peligros")
    if not checks["date"] or not checks["docs"]:
        laws.append("Requisitos locales de manifiestos y documentación")
    if not checks["roof"] or not checks["shelter"]:
        laws.append("Normas de almacenamiento y contención de materiales peligrosos")
    if not checks["segregation"]:
        laws.append("Requisitos de segregación y manejo de residuos")
    if not checks["nra"] or not checks["stamp"]:
        laws.append("Requisitos de identificación oficial, acuses y numeración documental")
    if not checks["inventory"]:
        laws.append("Requisitos de control y trazabilidad de residuos")
    if not checks["container"] or not checks["transfer"]:
        laws.append("Expectativas generales de transporte seguro y control de traslado")
    if not checks["destination"]:
        laws.append("Requisitos generales de disposición final y manejo responsable del residuo")
    if not checks["hazard_id"] or not checks["labels"]:
        laws.append("Requisitos generales de identificación del residuo y comunicación del riesgo")
    if not checks["spill_kit"]:
        laws.append("Expectativas generales de respuesta rápida ante derrames y contingencias")
    if not checks["closed_container"]:
        laws.append("Requisitos generales de integridad, cierre y protección del contenedor")
    if not checks["transport_control"] or not checks["disposal_evidence"]:
        laws.append("Requisitos generales de trazabilidad, transporte y evidencia de disposición final")
    return laws


def get_suggestions(checks: dict) -> list[str]:
    suggestions = []
    if not checks["containment"]:
        suggestions.append("Instale charolas o contenedores secundarios y verifique su integridad")
    if checks["spills"]:
        suggestions.append("Limpie el área afectada, retire material contaminado y revise la fuente del derrame")
    if not checks["labels"]:
        suggestions.append("Coloque etiquetas claras con contenido, símbolos de peligro y datos del responsable")
    if not checks["cretib"]:
        suggestions.append("Agregue el código CRETIB requerido y confirme que corresponda al residuo")
    if not checks["date"]:
        suggestions.append("Registre la fecha de generación en el contenedor o manifiesto")
    if not checks["docs"]:
        suggestions.append("Adjunte manifiesto, acuse o documentación de permiso correspondiente")
    if not checks["roof"] or not checks["shelter"]:
        suggestions.append("Proporcione almacenamiento cubierto o bajo techo para reducir la exposición")
    if not checks["segregation"]:
        suggestions.append("Separe corrientes incompatibles y etiquete cada sección con claridad")
    if not checks["nra"]:
        suggestions.append("Incluya y verifique el número NRA en la documentación correspondiente")
    if not checks["stamp"]:
        suggestions.append("Solicite y coloque el sello oficial SEMARNAT o Acuse cuando aplique")
    if not checks["inventory"]:
        suggestions.append("Mantenga un registro de inventario y trazabilidad del residuo")
    if not checks["container"]:
        suggestions.append("Inspeccione la integridad del contenedor antes del traslado y reemplace o repare los que presenten fuga o daño")
    if not checks["transfer"]:
        suggestions.append("Mantenga un registro claro de transferencia, responsable, fecha y destino intermedio o final")
    if not checks["destination"]:
        suggestions.append("Confirme el destino final o ruta de disposición y conserve evidencia de la misma")
    if not checks["hazard_id"]:
        suggestions.append("Identifique claramente el tipo de residuo, sus propiedades y el nivel de riesgo asociado")
    if not checks["spill_kit"]:
        suggestions.append("Disponga de materiales y procedimientos básicos para contener derrames y responder de forma rápida")
    if not checks["closed_container"]:
        suggestions.append("Mantenga el contenedor cerrado, protegido y en condiciones apropiadas para manejo y traslado")
    if not checks["transport_control"]:
        suggestions.append("Documente el transporte, la ruta, el responsable y el control de acceso al residuo")
    if not checks["disposal_evidence"]:
        suggestions.append("Conserve evidencia del destino final o disposición para fines de trazabilidad y revisión interna")
    return suggestions


col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📸 Evidencia fotográfica")
    st.caption("Suba una foto clara del contenedor, etiquetas, derrames o manifiesto.")
    img_file = st.file_uploader("Suba una foto del contenedor, etiquetas o manifiesto", type=["jpg", "jpeg", "png"])
    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="Evidencia cargada", use_container_width=True)

    if img_file and pipeline is not None:
        st.subheader("🤖 Análisis con IA")
        run_ai = st.checkbox("Intentar análisis automático de la imagen", value=False)
        if run_ai:
            with st.spinner("Analizando la imagen con un modelo local..."):
                try:
                    vision_pipeline = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
                    result = vision_pipeline(img)
                    ai_text = result[0]["generated_text"] if isinstance(result, list) and result else str(result)
                except Exception as exc:
                    ai_text = f"No fue posible completar el análisis automático: {exc}"
            st.info(ai_text)

    st.subheader("🧾 Lista de verificación")
    st.caption("Marque solo lo que sí se observa. Si algo no está claro, deje la casilla sin marcar.")
    with st.form("inspection_form"):
        st.markdown("<div style='background:#fff3f4;padding:12px 14px;border-radius:10px;border:1px solid #e7c9ce;margin:10px 0 8px 0;'><strong>1. Almacenamiento y manejo</strong><br>Inspección física del área, contenedores y condiciones de manejo.</div>", unsafe_allow_html=True)
        containment = st.checkbox("Hay contención secundaria o charola de derrames")
        spills = st.checkbox("Se observan derrames, manchas o fugas")
        roof = st.checkbox("Hay almacenamiento cubierto o bajo techo")
        shelter = st.checkbox("Hay protección contra intemperie")
        segregation = st.checkbox("Se observa segregación de residuos")
        inventory = st.checkbox("Hay inventario o control de residuos")

        st.markdown("<div style='background:#fff3f4;padding:12px 14px;border-radius:10px;border:1px solid #e7c9ce;margin:10px 0 8px 0;'><strong>2. Documentación y disposición</strong><br>Revisión de etiquetas, códigos, fechas, manifiestos y evidencia documental.</div>", unsafe_allow_html=True)
        labels = st.checkbox("Las etiquetas son visibles y legibles")
        cretib = st.checkbox("El código CRETIB es visible")
        date = st.checkbox("La fecha de generación es visible")
        docs = st.checkbox("Hay evidencia de manifiesto, acuse o permiso")
        nra = st.checkbox("Se observa número de registro o documento")
        stamp = st.checkbox("Se observa sello o acuse oficial visible")

        st.markdown("<div style='background:#fff3f4;padding:12px 14px;border-radius:10px;border:1px solid #e7c9ce;margin:10px 0 8px 0;'><strong>3. Transporte y destino final</strong><br>Control del traslado, ruta, contenedor y destino del residuo.</div>", unsafe_allow_html=True)
        container = st.checkbox("El contenedor se encuentra en buen estado para traslado")
        transfer = st.checkbox("Hay control de transferencia o cadena de custodia")
        destination = st.checkbox("Hay evidencia de destino final o ruta de disposición")
        transport_control = st.checkbox("Hay control claro del transporte o ruta")
        disposal_evidence = st.checkbox("Hay evidencia de disposición final o seguimiento")

        st.markdown("<div style='background:#fff3f4;padding:12px 14px;border-radius:10px;border:1px solid #e7c9ce;margin:10px 0 8px 0;'><strong>4. Riesgo y respuesta operativa</strong><br>Identificación del peligro y preparación básica para derrames o incidentes.</div>", unsafe_allow_html=True)
        hazard_id = st.checkbox("Se identifica claramente el tipo de residuo o riesgo")
        spill_kit = st.checkbox("Hay equipo o procedimiento para respuesta ante derrames")
        closed_container = st.checkbox("El contenedor está cerrado o protegido adecuadamente")

        st.markdown("<div style='background:#fff3f4;padding:12px 14px;border-radius:10px;border:1px solid #e7c9ce;margin:10px 0 8px 0;'><strong>5. Referencias generales</strong><br>Se consideran referencias generales para manejo ambiental, almacenamiento, etiquetado, transporte, trazabilidad y disposición final.</div>", unsafe_allow_html=True)
        st.caption("Incluye marcos federales y estatales comúnmente asociados a residuos y materiales peligrosos.")

        notes = st.text_area("Observaciones / Notes")
        submitted = st.form_submit_button("Generar informe")

    if submitted:
        checks = {
            "containment": containment,
            "spills": spills,
            "labels": labels,
            "cretib": cretib,
            "date": date,
            "docs": docs,
            "roof": roof,
            "shelter": shelter,
            "segregation": segregation,
            "nra": nra,
            "stamp": stamp,
            "inventory": inventory,
            "container": container,
            "transfer": transfer,
            "destination": destination,
            "hazard_id": hazard_id,
            "spill_kit": spill_kit,
            "closed_container": closed_container,
            "transport_control": transport_control,
            "disposal_evidence": disposal_evidence,
        }

        violations = get_violations(checks)
        laws = get_laws(checks)
        suggestions = get_suggestions(checks)

        score = 0
        if not containment:
            score += 25
        if spills:
            score += 25
        if not labels:
            score += 15
        if not cretib:
            score += 15
        if not date:
            score += 10
        if not docs:
            score += 15
        if not roof:
            score += 10
        if not shelter:
            score += 8
        if not segregation:
            score += 10
        if not nra:
            score += 8
        if not stamp:
            score += 8
        if not inventory:
            score += 8
        if not container:
            score += 8
        if not transfer:
            score += 8
        if not destination:
            score += 8
        if not hazard_id:
            score += 6
        if not spill_kit:
            score += 6
        if not closed_container:
            score += 6
        if not transport_control:
            score += 6
        if not disposal_evidence:
            score += 6

        risk_level = get_risk_level(score)

        report_text = "\n".join(
            [
                f"**Estado de cumplimiento:** {risk_level}",
                f"**Puntaje de riesgo:** {score}/100",
                "",
                "**Problemas observados:**",
                *([f"- {item}" for item in violations] if violations else ["- Ninguno detectado"]),
                "",
                "**Leyes o normas posibles implicadas:**",
                *([f"- {item}" for item in laws] if laws else ["- No se detectó incumplimiento mayor"]),
                "",
                "**Acciones correctivas sugeridas:**",
                *([f"- {item}" for item in suggestions] if suggestions else ["- No se requiere acción inmediata"]),
                "",
                f"**Observaciones:** {notes or 'No se proporcionaron observaciones adicionales.'}",
            ]
        )

        with col2:
            st.subheader("🔍 Informe de inspección")
            st.caption("Resultado generado a partir de la información registrada y la evidencia cargada.")
            st.markdown(f'<div class="report-card">{report_text}</div>', unsafe_allow_html=True)

            reports_dir = Path(__file__).resolve().parent / "data"
            reports_dir.mkdir(exist_ok=True)
            reports_file = reports_dir / "inspection_reports.csv"

            record = {
                "risk_level": risk_level,
                "risk_score": score,
                "containment": containment,
                "spills": spills,
                "labels": labels,
                "cretib": cretib,
                "date": date,
                "docs": docs,
                "roof": roof,
                "shelter": shelter,
                "segregation": segregation,
                "nra": nra,
                "stamp": stamp,
                "inventory": inventory,
                "container": container,
                "transfer": transfer,
                "destination": destination,
                "hazard_id": hazard_id,
                "spill_kit": spill_kit,
                "closed_container": closed_container,
                "transport_control": transport_control,
                "disposal_evidence": disposal_evidence,
                "violations": "; ".join(violations),
                "laws": "; ".join(laws),
                "suggestions": "; ".join(suggestions),
                "notes": notes,
            }

            if reports_file.exists():
                existing = pd.read_csv(reports_file)
            else:
                existing = pd.DataFrame()

            new_df = pd.DataFrame([record])
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined.to_csv(reports_file, index=False)

            st.success(f"Guardado en {reports_file}")
            st.download_button(
                label="Descargar informe como CSV (listo para Google Sheets)",
                data=combined.tail(1).to_csv(index=False).encode("utf-8"),
                file_name="inspection_report.csv",
                mime="text/csv",
            )

            st.markdown("---")
            st.caption("Aviso: esta herramienta es una nota de apoyo para autoevaluación y no sustituye una inspección legal, oficial, técnica o regulatoria. No representa una evaluación formal ni una recomendación de autoridad alguna. Las sugerencias son de carácter general y deben verificarse con personal ambiental competente y con la normativa aplicable a cada caso.")
