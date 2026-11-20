from calorvia_rag.config import runner_settings

import json

TRANSLATION_PROMPT = """Traduis la question en néerlandais et en anglais, sans y répondre.
Garde tels quels les noms propres, les codes, les nombres et les unités.
Réponds uniquement avec un objet JSON de la forme {"nl": "...", "en": "..."}."""

async def translate_question(query, llm_client):
    """{'fr': question, 'nl': …, 'en': …} ; seulement {'fr': question} si la réponse n'est pas un JSON valide."""
    response = await llm_client.chat.completions.create(
        model = runner_settings['generation']['model'],
        temperature = runner_settings['generation']['temperature'],
        messages = [
            {'role': 'system', 'content': TRANSLATION_PROMPT},
            {'role': 'user', 'content': query},
        ],
        response_format = {'type': 'json_object'},
        extra_body = {'chat_template_kwargs': {'enable_thinking': False}},   # pas de raisonnement : simple et rapide
    )
    try:
        translations = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {'fr': query}
    return {'fr': query, **{k: v for k, v in translations.items() if k in ('nl', 'en') and v}}
