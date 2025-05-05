from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
import re

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = FastAPI()

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Definir o modelo de dados para a requisição
class Query(BaseModel):
    query: str


# Carregar os dados da FURIA Esports
def load_furia_data():
    try:
        data_path = os.path.join(
            os.path.dirname(__file__), "data", "furia_esports.json"
        )
        with open(data_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Arquivo não encontrado. Verifique o caminho do arquivo.")
        return {}
    except json.JSONDecodeError:
        print("Erro ao decodificar o JSON. Verifique a formatação do arquivo.")
        return {}
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return {}


# Função para gerar o contexto com base nos dados da FURIA
def generate_context(furia_data: Dict[str, Any]) -> str:
    context = "Informações sobre a FURIA Esports:\n\n"

    # Adicionar informações gerais
    if "info" in furia_data:
        context += f"Sobre: {furia_data['info'].get('sobre', '')}\n"
        context += f"Fundada em: {furia_data['info'].get('fundada', '')}\n"

    # Adicionar informações dos times
    if "times" in furia_data:
        context += "\nTimes:\n"
        for jogo, info in furia_data["times"].items():
            context += f"\n{jogo}:\n"
            context += f"- Lineup: {', '.join(info.get('lineup', []))}\n"
            context += f"- Campeonatos: {', '.join(info.get('campeonatos', []))}\n"
            if "conquistas" in info:
                context += "- Conquistas:\n"
                for conquista in info.get("conquistas", []):
                    context += f"  * {conquista}\n"

    # Adicionar histórico de competições
    if "competicoes" in furia_data:
        context += "\nPrincipais Competições:\n"
        for comp in furia_data["competicoes"]:
            context += f"- {comp.get('nome', '')}: {comp.get('resultado', '')}\n"

    # Processar dados do furia_esports.json (versão 2025)
    if "FURIA_Esports_2025" in furia_data:
        furia_2025 = furia_data["FURIA_Esports_2025"]

        # League of Legends
        if "League_of_Legends" in furia_2025:
            lol_data = furia_2025["League_of_Legends"]
            context += "\nLeague of Legends (2025):\n"
            if "lineup" in lol_data:
                lineup = lol_data["lineup"]
                context += f"- Lineup atual: {lineup.get('top', '')} (Top), {lineup.get('jungle', '')} (Jungle), "
                context += f"{lineup.get('mid', '')} (Mid), {lineup.get('adc', '')} (ADC), {lineup.get('support', '')} (Support)\n"

            if "coaching_staff" in lol_data:
                coaches = lol_data["coaching_staff"]
                context += f"- Comissão Técnica: {coaches.get('head_coach', '')} (Head Coach), "
                context += f"{coaches.get('assistant_coach', '')} (Assistant Coach)\n"

            if "latest_competition" in lol_data:
                comp = lol_data["latest_competition"]
                context += f"- Competição atual: {comp.get('name', '')}\n"

        # Counter Strike 2
        if "Counter_Strike_2" in furia_2025:
            cs_data = furia_2025["Counter_Strike_2"]
            context += "\nCounter Strike 2 (2025):\n"
            if "lineup" in cs_data:
                context += f"- Lineup atual: {', '.join(cs_data['lineup'])}\n"

            if "coaching_staff" in cs_data:
                coaches = cs_data["coaching_staff"]
                context += f"- Comissão Técnica: {coaches.get('head_coach', '')} (Head Coach), "
                context += f"{coaches.get('assistant_coach', '')} (Assistant Coach)\n"

            if "latest_competition" in cs_data:
                comp = cs_data["latest_competition"]
                context += f"- Competição recente: {comp.get('name', '')}, Resultado: {comp.get('result', '')}\n"

            if "notes" in cs_data:
                context += "- Notas: " + "; ".join(cs_data["notes"]) + "\n"

        # Valorant
        if "Valorant" in furia_2025:
            val_data = furia_2025["Valorant"]
            context += "\nValorant (2025):\n"
            if "lineup" in val_data:
                context += f"- Lineup atual: {', '.join(val_data['lineup'])}\n"

            if "coaching_staff" in val_data:
                coaches = val_data["coaching_staff"]
                context += f"- Comissão Técnica: {coaches.get('head_coach', '')} (Head Coach)\n"

            if "academy_team" in val_data:
                academy = val_data["academy_team"]
                context += f"- Time Academy: {', '.join(academy.get('players', []))}, Coach: {academy.get('coach', '')}\n"

            if "notes" in val_data:
                context += "- Notas: " + "; ".join(val_data["notes"]) + "\n"

        # Conquistas históricas
        if "historical_titles" in furia_2025:
            titles = furia_2025["historical_titles"]
            context += "\nConquistas Históricas:\n"

            for game, achievements in titles.items():
                context += f"\n{game.replace('_', ' ')}:\n"
                for achievement in achievements:
                    context += f"- {achievement.get('year', '')}: {achievement.get('title', '')}\n"

        # Estatísticas
        if "statistics" in furia_2025:
            stats = furia_2025["statistics"]
            context += "\nEstatísticas de Jogadores:\n"

            for game, players in stats.items():
                context += f"\n{game.replace('_', ' ')}:\n"
                for player, player_stats in players.items():
                    context += f"- {player}: "
                    stats_list = []
                    for stat_name, stat_value in player_stats.items():
                        stats_list.append(f"{stat_name}: {stat_value}")
                    context += ", ".join(stats_list) + "\n"

    return context


# Inicializar o cliente OpenAI com a API key do ambiente
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("AVISO: OPENAI_API_KEY não encontrada no ambiente.")
        api_key = ""  # Valor vazio para fallback

    # Criar cliente sem argumentos adicionais
    return OpenAI(api_key=api_key)


# Base de conhecimento para respostas sem OpenAI
KNOWLEDGE_BASE = {
    # CS2 / Counter Strike
    "cs2_lineup": "Nosso time de CS2 é composto por KSCERATO, yuurih, FalleN, chelo e skullz. Eles são considerados um dos melhores times do Brasil e competem nos maiores torneios internacionais.",
    "cs2_coach": "A comissão técnica de CS2 é liderada por sidde como head coach, com Lucid como assistente técnico e innersh1ne como analista.",
    "cs2_achievements": "Entre as conquistas no CS2/CSGO estão: ESL Pro League Season 12 North America (2020), IEM Fall North America (2021) e CBCS Elite League Season 2 (2022). Também fomos finalistas da IEM Dallas 2022.",
    "cs2_competitions": "Nossa equipe de CS2 compete em torneios como ESL Pro League, BLAST Premier, IEM e campeonatos regionais como a CBCS.",
    "cs2_player_kscerato": "KSCERATO é um dos principais jogadores da FURIA, com rating médio de 1.18, 0.14 entry kills por round e K/D ratio de 1.3. Ele renovou contrato por 3 anos.",
    "cs2_player_fallen": "FalleN é um veterano lendário do CS brasileiro que se juntou à FURIA. Ele mantém um rating de 1.02, com 0.08 entry kills por round e K/D ratio de 1.05.",
    "cs2_player_yuurih": "yuurih é um dos pilares da FURIA CS2, conhecido por sua consistência. Ele recentemente renovou seu contrato por 3 anos com a organização.",
    "cs2_recent": "Recentemente nossa equipe de CS2 participou da Esports World Cup em Riade, onde fomos eliminados pela NAVI.",
    "cs2_changes": "A mudança mais recente no nosso time de CS2 foi a saída de arT (que foi para o Fluxo) e a entrada de skullz na equipe.",
    # League of Legends
    "lol_lineup": "Nosso time de League of Legends que compete no CBLOL é formado por Guigo (Top), Tatu (Jungle), Tutsz (Mid), Ayu (ADC) e JoJo (Support).",
    "lol_coach": "A comissão técnica de League of Legends é liderada por Thinkcard como head coach, com furyz como assistente técnico e Maestro como gerente geral.",
    "lol_achievements": "No League of Legends, conquistamos o CBLOL Academy 1° Split 2022 e o CBLOL Academy 2° Split 2023. Além disso, chegamos ao Top 4 no CBLOL 2023.",
    "lol_competitions": "Nossa equipe de LoL compete principalmente no CBLOL (Campeonato Brasileiro de League of Legends) e no CBLOL Academy.",
    "lol_recent": "Nossa equipe está se preparando para a LTA Sul 2025, com o sorteio marcado para 18 de janeiro de 2025 e início em 25 de janeiro de 2025.",
    "lol_player_ayu": "Ayu é nosso atirador (ADC), com bom posicionamento e mecânica apurada. Ele mantém um KDA de 5.1, participação em kills de 72% e 540 de dano por minuto.",
    "lol_player_tutsz": "Tutsz é nosso mid laner versátil com experiência no CBLOL. Ele tem um KDA de 4.3, participação em kills de 68% e 490 de dano por minuto.",
    "lol_changes": "Em 2025, retornamos à comunicação em português e formamos uma equipe que combina experiência e novos talentos.",
    "lol_previous": "Na temporada anterior (CBLOL 2024), nosso time era composto por Zzk (Top), Wiz (Jungle), Tutsz (Mid), Ayu (ADC) e JoJo (Support), com Westonway como técnico.",
    # Valorant
    "valorant_lineup": "A equipe principal de Valorant da FURIA é composta por khalil, havoc, heat, raafa e pryze.",
    "valorant_coach": "O head coach da nossa equipe de Valorant é peu, que lidera a comissão técnica.",
    "valorant_academy": "Temos também um time academy de Valorant formado por Above, Desire, Loss, skz e swag, com ryotzz como treinador.",
    "valorant_achievements": "No Valorant, fomos campeões do VCT Challengers Brazil em 2021 e finalistas do VCT Brazil Playoffs em 2022. Também alcançamos o Top 8 no VCT Americas 2023.",
    "valorant_competitions": "Nossa equipe de Valorant compete no VCT Americas e no Challengers BR.",
    "valorant_player_heat": "heat é um dos nossos principais jogadores de Valorant, com ACS de 240, KDA de 1.25 e 27% de headshot.",
    "valorant_player_raafa": "raafa traz experiência e liderança ao time de Valorant, com ACS de 210, KDA de 1.30 e 25% de headshot.",
    "valorant_changes": "Atualmente mwzera está afastado temporariamente por questões de saúde, enquanto heat e raafa trazem experiência e liderança ao time.",
    # Informações gerais
    "furia_history": "A FURIA Esports é uma organização brasileira de esportes eletrônicos fundada em 2017. Nos destacamos em modalidades como CS2, League of Legends e Valorant.",
    "furia_branding": "Nossa identidade visual é caracterizada pelo preto como cor primária e branco como secundária, com a pantera como símbolo e um estilo agressivo e moderno.",
    "furia_other": "A FURIA já teve times em outras modalidades como Rocket League (último evento: RLCS South America 2022) e Rainbow Six Siege (último evento: Brasileirão R6 2022), que atualmente estão inativos.",
    # Respostas gerais
    "default": "Sou o chatbot oficial da FURIA Esports. Posso fornecer informações sobre nossos times de League of Legends, Counter Strike 2 e Valorant. Como posso ajudar você hoje?",
    "unknown": "Não tenho essa informação específica no momento. Posso ajudar com detalhes sobre nossos times atuais de CS2, League of Legends e Valorant, ou sobre a história da FURIA. O que você gostaria de saber?",
    "greeting": "E aí! Tudo bem? Sou o bot oficial da FURIA Esports, pronto pra te ajudar com informações sobre nossos times e jogadores. O que você quer saber sobre a pantera? 🐾🖤",
    "thanks": "Por nada! Sempre à disposição para falar sobre a FURIA. Se tiver mais perguntas, é só chamar! #GoPantera 🖤",
    "goodbye": "Valeu pela conversa! Se precisar de mais informações sobre a FURIA, é só voltar. #SomosFURIA 🐾",
}

# Lista de palavras-chave e frases para identificar intenções
INTENT_PATTERNS = {
    # CS2 / Counter Strike
    "cs2_lineup": [
        r"(line(\s)?up|elenco|jogadores|integrantes|time).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(line(\s)?up|elenco|jogadores|integrantes|time)",
        r"quem.*(joga|está).*(cs|counter|cs2)",
        r"quem.*(é|são).*jogadores.*(cs|counter|cs2)",
    ],
    "cs2_coach": [
        r"(técnico|coach|treinador|comissão).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(técnico|coach|treinador|comissão)",
        r"quem.*(treina|comanda).*(cs|counter|cs2)",
    ],
    "cs2_achievements": [
        r"(conquistas|títulos|troféus|vitórias|campeonatos).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(conquistas|títulos|troféus|vitórias|campeonatos)",
        r"(cs|counter|cs2).*(ganhou|venceu|conquistou)",
    ],
    "cs2_competitions": [
        r"(competições|torneios|campeonatos|disputam).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(competições|torneios|campeonatos|disputam)",
    ],
    "cs2_player_kscerato": [r"kscerato"],
    "cs2_player_fallen": [r"fallen"],
    "cs2_player_yuurih": [r"yuurih"],
    "cs2_recent": [
        r"(recente|última|recém).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(recente|última|recém)",
        r"como.*(foi|está).*(cs|counter|cs2)",
    ],
    "cs2_changes": [
        r"(mudanças|alterações|trocas|substituições).*(cs|counter|cs2)",
        r"(cs|counter|cs2).*(mudanças|alterações|trocas|substituições)",
    ],
    # League of Legends
    "lol_lineup": [
        r"(line(\s)?up|elenco|jogadores|integrantes|time).*(lol|league|legends)",
        r"(lol|league|legends).*(line(\s)?up|elenco|jogadores|integrantes|time)",
        r"quem.*(joga|está).*(lol|league|legends)",
        r"quem.*(é|são).*jogadores.*(lol|league|legends)",
    ],
    "lol_coach": [
        r"(técnico|coach|treinador|comissão).*(lol|league|legends)",
        r"(lol|league|legends).*(técnico|coach|treinador|comissão)",
        r"quem.*(treina|comanda).*(lol|league|legends)",
    ],
    "lol_achievements": [
        r"(conquistas|títulos|troféus|vitórias|campeonatos).*(lol|league|legends)",
        r"(lol|league|legends).*(conquistas|títulos|troféus|vitórias|campeonatos)",
        r"(lol|league|legends).*(ganhou|venceu|conquistou)",
    ],
    "lol_competitions": [
        r"(competições|torneios|campeonatos|disputam).*(lol|league|legends)",
        r"(lol|league|legends).*(competições|torneios|campeonatos|disputam)",
    ],
    "lol_recent": [
        r"(recente|última|recém|próxima).*(lol|league|legends)",
        r"(lol|league|legends).*(recente|última|recém|próxima)",
        r"como.*(foi|está).*(lol|league|legends)",
    ],
    "lol_player_ayu": [r"ayu"],
    "lol_player_tutsz": [r"tutsz"],
    "lol_changes": [
        r"(mudanças|alterações|trocas|substituições).*(lol|league|legends)",
        r"(lol|league|legends).*(mudanças|alterações|trocas|substituições)",
    ],
    "lol_previous": [
        r"(antiga|anterior|passada|2024).*(lol|league|legends)",
        r"(lol|league|legends).*(antiga|anterior|passada|2024)",
    ],
    # Valorant
    "valorant_lineup": [
        r"(line(\s)?up|elenco|jogadores|integrantes|time).*(val|valorant)",
        r"(val|valorant).*(line(\s)?up|elenco|jogadores|integrantes|time)",
        r"quem.*(joga|está).*(val|valorant)",
        r"quem.*(é|são).*jogadores.*(val|valorant)",
    ],
    "valorant_coach": [
        r"(técnico|coach|treinador|comissão).*(val|valorant)",
        r"(val|valorant).*(técnico|coach|treinador|comissão)",
        r"quem.*(treina|comanda).*(val|valorant)",
    ],
    "valorant_academy": [
        r"(academy|base|jovem).*(val|valorant)",
        r"(val|valorant).*(academy|base|jovem)",
    ],
    "valorant_achievements": [
        r"(conquistas|títulos|troféus|vitórias|campeonatos).*(val|valorant)",
        r"(val|valorant).*(conquistas|títulos|troféus|vitórias|campeonatos)",
        r"(val|valorant).*(ganhou|venceu|conquistou)",
    ],
    "valorant_competitions": [
        r"(competições|torneios|campeonatos|disputam).*(val|valorant)",
        r"(val|valorant).*(competições|torneios|campeonatos|disputam)",
    ],
    "valorant_player_heat": [r"heat"],
    "valorant_player_raafa": [r"raafa"],
    "valorant_changes": [
        r"(mudanças|alterações|trocas|substituições).*(val|valorant)",
        r"(val|valorant).*(mudanças|alterações|trocas|substituições)",
        r"mwzera",
    ],
    # Informações gerais
    "furia_history": [
        r"(história|fundação|fundada|sobre).*(furia|pantera)",
        r"quando.*(foi|surgiu|nasceu|criada)",
        r"quem.*(fundou|criou)",
    ],
    "furia_branding": [
        r"(logo|marca|símbolo|cor|visual|identidade|mascote)",
        r"pantera",
    ],
    "furia_other": [
        r"(outros|outras).*(jogos|modalidades|esports)",
        r"(rocket|r6|rainbow|siege)",
    ],
    # Respostas gerais
    "greeting": [
        r"^(oi|olá|e aí|salve|opa|eae|beleza|tudo bem|como vai)",
        r"(oi|olá|e aí|salve|opa|eae|beleza)$",
    ],
    "thanks": [
        r"(obrigad|valeu|agradec|thanks|brigad|vlw)",
        r"(obrigad|valeu|agradec|thanks|brigad|vlw)$",
    ],
    "goodbye": [r"^(tchau|adeus|até|flw|falou)", r"(tchau|adeus|até|flw|falou)$"],
}


# Função avançada de fallback para processar perguntas sem usar a OpenAI
def advanced_fallback_response(query: str) -> str:
    query_lower = query.lower()

    # Identificar intenções baseadas em padrões de regex
    matched_intents = []

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                matched_intents.append(intent)
                break

    # Se encontrou correspondências específicas
    responses = []
    if matched_intents:
        for intent in matched_intents:
            if intent in KNOWLEDGE_BASE:
                responses.append(KNOWLEDGE_BASE[intent])

    # Verificar palavras-chave gerais se não encontrou correspondências específicas
    if not responses:
        # Verificar CS2
        if any(
            keyword in query_lower
            for keyword in ["cs", "cs2", "counter", "counter-strike", "fps"]
        ):
            responses.append(KNOWLEDGE_BASE["cs2_lineup"])

        # Verificar LoL
        elif any(
            keyword in query_lower for keyword in ["lol", "league", "legends", "moba"]
        ):
            responses.append(KNOWLEDGE_BASE["lol_lineup"])

        # Verificar Valorant
        elif any(keyword in query_lower for keyword in ["val", "valorant"]):
            responses.append(KNOWLEDGE_BASE["valorant_lineup"])

        # Resposta padrão se nada for identificado
        else:
            responses.append(KNOWLEDGE_BASE["default"])

    # Combinar respostas (limite a 2 para não ficar muito longo)
    if len(responses) > 2:
        responses = responses[:2]

    # Formatar resposta final
    response = " ".join(responses)

    return response


# Endpoint para processar consultas ao bot
@app.post("/query")
async def process_query(query: Query):
    try:
        # Tentar usar OpenAI se a chave estiver disponível
        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key and not api_key.strip() == "":
            try:
                # Carregar dados e gerar contexto
                furia_data = load_furia_data()
                if not furia_data:
                    raise HTTPException(
                        status_code=500,
                        detail="Não foi possível carregar os dados da FURIA",
                    )

                context = generate_context(furia_data)

                # Configurar o prompt para o modelo OpenAI
                system_prompt = (
                    "Você é o chatbot oficial da FURIA Esports. Responda de forma amigável, "
                    "informativa e concisa às perguntas sobre a FURIA, seus times de esports, "
                    "jogadores e competições. Use um tom jovem e entusiasmado, próprio do mundo "
                    "dos esports. Se não souber a resposta com base no contexto fornecido, "
                    "informe educadamente que não tem essa informação específica e ofereça "
                    "redirecionar para outras informações que você possui."
                )

                client = OpenAI(api_key=api_key)

                # Fazer requisição para a OpenAI
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "system", "content": f"Contexto: {context}"},
                        {"role": "user", "content": query.query},
                    ],
                )

                # Extrair a resposta
                answer = completion.choices[0].message.content

                return {"answer": answer}

            except Exception as e:
                print(f"Erro na comunicação com OpenAI: {e}")
                # Cair no fallback se houver erro na API
                return {"answer": advanced_fallback_response(query.query)}
        else:
            # Usar o fallback avançado se não tiver API key
            return {"answer": advanced_fallback_response(query.query)}

    except Exception as e:
        print(f"Erro no processamento da consulta: {e}")
        return {"answer": KNOWLEDGE_BASE["default"]}


# Rota para verificar a saúde do serviço
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Iniciar o servidor se este arquivo for executado diretamente
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
