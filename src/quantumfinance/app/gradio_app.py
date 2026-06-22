"""Interface conversacional Gradio do QuantumFinance AI Agent."""

import re
from functools import partial

import gradio as gr
from langchain_core.messages import HumanMessage

from quantumfinance.agents.orchestrator import app
from quantumfinance.output.storage import load_recommendations
from quantumfinance.universe import TICKERS

EXAMPLE_QUESTIONS = [
    "Qual a recomendação para PETR4 hoje?",
    "Compare os indicadores de VALE3 e PETR4",
    "Qual o sentimento das notícias sobre BBAS3?",
    "Por que você recomendaria comprar ITUB4?",
]

TICKER_PATTERN = re.compile(r"\b[A-Z]{4}\d{1,2}\b")
REASONING_TAGS = [("<thinking>", "</thinking>")]

FALLBACK_EMPTY_RESPONSE = "O sistema não conseguiu gerar uma resposta para essa pergunta. Tente reformular."
FALLBACK_CONNECTION_ERROR = "Serviço temporariamente indisponível. Tente novamente em alguns instantes."
FALLBACK_UNEXPECTED_ERROR = "Não foi possível processar sua pergunta agora. Tente novamente."
NO_TRACE_MESSAGE = "Nenhuma etapa intermediária registrada para esta pergunta."


def find_unmonitored_ticker(question: str) -> str | None:
    """Identifica um ticker citado na pergunta que não está no universo monitorado."""
    for match in TICKER_PATTERN.findall(question.upper()):
        if match not in TICKERS:
            return match
    return None


def build_trace(messages: list) -> str:
    """Monta um resumo legível das etapas intermediárias (tool calls e respostas) do agente."""
    lines = []
    for message in messages:
        message_type = type(message).__name__
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            for call in tool_calls:
                lines.append(f"🔧 Chamou `{call['name']}` com args `{call['args']}`")
        elif message_type == "ToolMessage":
            lines.append(f"📥 Resultado da tool: {message.content}")
        elif message_type == "AIMessage" and message.content:
            lines.append(f"💬 {message.content}")
    return "\n\n".join(lines) if lines else NO_TRACE_MESSAGE


def safe_ask(question: str) -> tuple[str, str]:
    """Envia a pergunta ao orquestrador, sempre retornando mensagens amigáveis em caso de erro."""
    unmonitored = find_unmonitored_ticker(question)
    if unmonitored:
        message = f"Ticker não monitorado: {unmonitored}. Tickers disponíveis: {', '.join(TICKERS)}."
        return message, "Pergunta não enviada ao agente — ticker fora do universo monitorado."

    try:
        result = app.invoke({"messages": [HumanMessage(content=question)]})
    except Exception as e:
        error_text = str(e).lower()
        is_connection_error = any(
            keyword in error_text
            for keyword in ("connect", "timeout", "timed out", "unavailable", "502", "503")
        )
        friendly = FALLBACK_CONNECTION_ERROR if is_connection_error else FALLBACK_UNEXPECTED_ERROR
        return friendly, f"Erro ao processar a pergunta: {e}"

    messages = result.get("messages", [])
    final_answer = messages[-1].content if messages else ""
    if not isinstance(final_answer, str) or not final_answer.strip():
        final_answer = FALLBACK_EMPTY_RESPONSE

    return final_answer, build_trace(messages)


def format_sidebar() -> str:
    """Formata as últimas 5 recomendações do CSV para exibição na barra lateral."""
    rows = load_recommendations()
    if not rows:
        return "_Nenhuma recomendação registrada ainda. Faça uma pergunta de recomendação completa para começar o histórico._"

    last_five = list(reversed(rows[-5:]))
    lines = ["| Ticker | Data | Recomendação | Confiança |", "|---|---|---|---|"]
    for row in last_five:
        lines.append(f"| {row['ticker']} | {row['date']} | {row['recommendation']} | {row['confidence']} |")
    return "\n".join(lines)


def respond(question: str, history: list[dict]) -> tuple[list[dict], str, str]:
    """Processa a pergunta do usuário e atualiza conversa e barra lateral.

    O raciocínio do agente vai embutido em tags <thinking> no conteúdo da
    mensagem; o gr.Chatbot (reasoning_tags) extrai isso automaticamente e
    exibe como uma bolha colapsável "Reasoning" antes da resposta final.
    """
    if not question or not question.strip():
        return history, "", format_sidebar()

    answer, trace = safe_ask(question)
    assistant_content = f"<thinking>{trace}</thinking>{answer}"
    new_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": assistant_content},
    ]
    return new_history, "", format_sidebar()


def clear_conversation() -> tuple[list[dict], str, str]:
    """Limpa a conversa, mantendo a barra lateral atualizada."""
    return [], "", format_sidebar()


with gr.Blocks(title="QuantumFinance AI Agent") as demo:
    gr.Markdown(
        "# QuantumFinance AI Agent\n"
        "Recomendações de **PETR4**, **VALE3**, **BBAS3** e **ITUB4** combinando "
        "indicadores técnicos e sentimento de notícias, com justificativa auditável."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversa", height=450, reasoning_tags=REASONING_TAGS)
            question_box = gr.Textbox(
                label="Sua pergunta",
                placeholder="Ex: Qual a recomendação para PETR4 hoje?",
            )
            with gr.Row():
                send_btn = gr.Button("Enviar", variant="primary")
                clear_btn = gr.Button("Limpar conversa")

            gr.Markdown("**Exemplos:**")
            with gr.Row():
                example_buttons = [gr.Button(question, size="sm") for question in EXAMPLE_QUESTIONS]

        with gr.Column(scale=1):
            gr.Markdown("### Últimas recomendações")
            sidebar_box = gr.Markdown(format_sidebar())

    send_btn.click(
        fn=respond,
        inputs=[question_box, chatbot],
        outputs=[chatbot, question_box, sidebar_box],
    )
    question_box.submit(
        fn=respond,
        inputs=[question_box, chatbot],
        outputs=[chatbot, question_box, sidebar_box],
    )
    clear_btn.click(
        fn=clear_conversation,
        outputs=[chatbot, question_box, sidebar_box],
    )
    for button, example_question in zip(example_buttons, EXAMPLE_QUESTIONS):
        button.click(
            fn=partial(respond, example_question),
            inputs=[chatbot],
            outputs=[chatbot, question_box, sidebar_box],
        )


if __name__ == "__main__":
    demo.launch()
