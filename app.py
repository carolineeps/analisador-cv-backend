# backend/app.py - VERSÃO FINAL E CORRIGIDA

import os
import io
import re
import unicodedata
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import docx2txt

# --- Inicialização ---
app = Flask(__name__)
CORS(app)

# --- MAPA DE COMPETÊNCIAS ---
KEYWORDS_MAP_POR_NIVEL = {
    "estagiario": {"Lançamentos e Conciliações": ["lançamento", "lançamentos", "conciliação", "conciliações"], "Organização de Documentos": ["arquivo", "documento", "organização"], "Rotinas Financeiras": ["contas a pagar", "contas a receber", "fluxo de caixa"], "Excel / Planilhas": ["excel", "planilha", "planilhas"]},
    "assistente": {"Conciliação Bancária": ["conciliação bancária"], "Documentos Fiscais": ["nota fiscal", "nf-e", "danfe"], "Apuração de Impostos": ["imposto", "impostos", "retenção na fonte", "icms", "ipi", "pis", "cofins"], "Obrigações Acessórias": ["sped", "dctf", "ecf"], "Sistemas ERP": ["erp", "totvs", "sap", "oracle"]},
    "analista_junior": {"Análise de Contas": ["análise de conta", "análise de contas", "análise de dados contábeis", "conciliação de contas"], "Fechamento Contábil": ["fechamento contábil", "fechamento mensal"], "Relatórios Contábeis": ["dre", "balancete", "demonstração de resultado"], "Regime Tributário": ["lucro real", "lucro presumido"], "Excel Avançado": ["excel avançado", "tabela dinâmica", "procv"], "CRC": ["crc", "crc ativo", "conselho regional de contabilidade"]},
    "analista_pleno": {"Demonstrações Financeiras": ["demonstração financeira", "demonstrações financeiras", "dfc", "dlpa", "dmpl"], "Balanço Patrimonial": ["balanço patrimonial"], "Normas Contábeis (BR GAAP)": ["cpc", "cpcs"], "Normas Contábeis (IFRS)": ["ifrs", "normas contábeis"], "Análise de Variações": ["análise de variação", "variação orçamentária"], "Business Intelligence": ["power bi", "tableau", "qlik"]},
    "analista_senior": {"Consolidação de Balanços": ["consolidação de balanço", "consolidado", "consolidações"], "Relatórios Gerenciais": ["relatório gerencial", "report gerencial", "relatórios gerenciais"], "Planejamento Tributário": ["planejamento tributário", "elisão fiscal"], "Auditoria": ["auditoria externa", "auditoria interna", "pwc", "deloitte", "ey", "kpmg"], "Controles Internos": ["controle interno", "controles internos", "processos e controles internos"], "Preços de Transferência": ["preço de transferência", "transfer price"], "KPIs": ["kpi", "kpis", "indicador de desempenho"], "Contabilidade de Custos": ["custo", "custeio", "contabilidade de custo"], "Pós-Graduação/Especialização Relevante": ["pós-graduação", "especialização", "mba", "controladoria", "finanças", "tributário"]},
    "especialista": {"Normas Contábeis Complexas": ["normas contábeis", "ifrs", "cpc", "usgaap", "conformidade normativa"], "Consultoria": ["consultoria", "consultor", "consultora"], "Revisão de Processos": ["revisão de processo", "melhoria contínua", "automação de rotinas", "automação de processos contábeis"], "Reporte Internacional": ["reporte internacional", "relatórios em inglês", "matriz"], "Due Diligence": ["due diligence", "fusões e aquisições"], "SOX": ["sox", "sarbanes-oxley"], "Laudo Contábil": ["laudo contábil", "perícia contábil", "memorandos técnicos"], "Pós-Graduação/Especialização Relevante": ["pós-graduação", "especialização", "mba", "controladoria", "finanças", "tributário", "contabilidade estratégica"]},
    "consultor": {"Diagnósticos Financeiros": ["diagnóstico financeiro", "diagnóstico empresarial"], "Otimização de Processos": ["otimização de processo"], "Gestão de Projetos": ["gestão de projeto", "pmo", "cronograma", "liderança de projetos"], "Reestruturação Societária": ["reestruturação societária"], "Valuation": ["valuation", "avaliação de empresas"], "Modelagem Financeira": ["modelagem financeira"], "M&A (Fusões e Aquisições)": ["m&a", "fusões e aquisições"]},
    "supervisor": {"Supervisão de Equipe": ["supervisão de equipe", "supervisor", "liderança"], "Revisão do Fechamento": ["revisão do fechamento", "revisão de lançamentos"], "Delegação de Tarefas": ["delegação", "distribuição de tarefas"], "Treinamento e Desenvolvimento": ["treinamento", "desenvolvimento de equipe"], "Gestão de Prazos": ["prazo", "cronograma", "deadline"], "Melhoria Contínua": ["melhoria contínua"]},
    "coordenador": {"Coordenação de Equipes": ["coordenação", "coordenador", "coordenar equipe"], "Gestão de Processos Contábeis": ["gestão de processo", "processos contábeis"], "Orçamento (Budget/Forecast)": ["orçamento", "budget", "forecast"], "Relacionamento com Auditoria": ["auditoria externa", "auditorias"], "Report Gerencial": ["report gerencial", "apresentação para gerência"], "Relacionamento Interdepartamental": ["interdepartamental", "interface com áreas"]},
    "gerente": {"Gestão Estratégica": ["gestão estratégica", "planejamento estratégico"], "Planejamento Financeiro": ["planejamento financeiro"], "Report à Diretoria": ["report à diretoria", "apresentação para diretoria"], "Liderança": ["liderança", "líder"], "Tomada de Decisão": ["tomada de decisão"], "Gestão de Stakeholders": ["stakeholder", "stakeholders"], "Controle Orçamentário": ["controle orçamentário"]}
}
SECOES_ESPERADAS = ["resumo", "experiência", "formação", "acadêmica", "habilidade", "competência", "idioma", "curso", "certificação", "projeto", "recomendação"]

# FUNÇÃO CORRIGIDA QUE SERÁ USADA
def normalizar_texto_universal(texto):
    texto = str(texto).lower()
    # Remove acentos
    nfkd_form = unicodedata.normalize('NFD', texto)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove caracteres não alfanuméricos e espaços
    texto_final = re.sub(r'[^a-z0-9]', '', texto_sem_acento)
    return texto_final

def extrair_texto(file_stream, filename):
    texto_bruto = ""
    try:
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file_stream)
            texto_bruto = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        elif filename.endswith('.docx'):
            texto_bruto = docx2txt.process(file_stream)
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
    return texto_bruto

@app.route('/analisar', methods=['POST'])
def analisar():
    if 'cv' not in request.files: return jsonify({"erro": "Nenhum arquivo de currículo enviado."}), 400

    file = request.files['cv']
    nivel_vaga = request.form.get('nivel', 'analista_senior')
    
    texto_bruto_cv = extrair_texto(io.BytesIO(file.read()), file.filename)
    if not texto_bruto_cv: return jsonify({"erro": "Não foi possível ler o conteúdo do arquivo."}), 400

    texto_cv_universal = normalizar_texto_universal(texto_bruto_cv)
    
    mapa_para_analise = KEYWORDS_MAP_POR_NIVEL.get(nivel_vaga, {})
    
    encontradas_kw, faltantes_kw = [], []

    if mapa_para_analise:
        for conceito, variacoes in mapa_para_analise.items():
            # A LÓGICA DE COMPARAÇÃO FOI CORRIGIDA AQUI
            if any(normalizar_texto_universal(var) in texto_cv_universal for var in variacoes):
                encontradas_kw.append(conceito)
            else:
                faltantes_kw.append(conceito)
    
    conceitos_a_analisar = list(mapa_para_analise.keys())
    score_kw = (len(encontradas_kw) / len(conceitos_a_analisar)) * 100 if conceitos_a_analisar else 100
    
    texto_cv_limpo_com_espacos = re.sub(r'\s+', ' ', texto_bruto_cv.lower())
    encontradas_secoes = [secao for secao in SECOES_ESPERADAS if secao in texto_cv_limpo_com_espacos]
    score_estrutura = min((len(set(encontradas_secoes)) / 5) * 100, 100)

    score_final = (score_kw * 0.7) + (score_estrutura * 0.3)
    
    feedback_geral = "Atenção! Risco de descarte automático."
    if score_final >= 80: feedback_geral = "Excelente compatibilidade!"
    elif score_final >= 60: feedback_geral = "Bom, mas pode melhorar."

    relatorio = {
        "scoreFinal": round(score_final), "feedbackGeral": feedback_geral,
        "analiseKeywords": {"encontradas": encontradas_kw, "sugeridas": faltantes_kw},
        "analiseEstrutura": {"score": round(score_estrutura), "dica": "Ótima estrutura!"},
        "vagaAnalisada": False
    }
    return jsonify(relatorio)

@app.route('/')
def index():
    return "Backend do Analisador de CV está no ar!"

if __name__ == '__main__':
    app.run(debug=True)
