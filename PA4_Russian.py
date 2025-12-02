import google.generativeai as genai
import pandas as pd
from pandas import json_normalize
import json
import streamlit as st
import re


st.set_page_config(layout="wide")

st.markdown("""
        <style>
            .block-container {
                padding-left: 10rem;
                padding-right: 10rem;
            }
        </style>
        """, unsafe_allow_html=True)
st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")


st.markdown("<h1 span style='color: #B984DB;'>Russian Verb Conjugator</span>", unsafe_allow_html=True)
st.divider()
st.header("This application will help you extract the verb from the text, conjugate them for you and give you some examples! Simply put your text in the box and we're ready to go!")

st.write('**<u>Note</u>** In Russian, the imperfective aspect forms the present tense (ongoing or habitual action) and a simple ' \
'future tense (using "to be" + infinitive for future events). The perfective aspect does not have a present tense. ' \
'Its present-looking forms are actually a future-tense simple form (with a completed meaning), and it forms a more common ' \
'future tense with a completed or one-time meaning', unsafe_allow_html=True)

#API, INPUT and PROMPT
api_key = None
with st.sidebar:
    st.header('API key🔑')
    api_key = st.text_input("Enter your API Key", type="password", placeholder="Your API key")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-lite") 
        is_model_ready = True
    except Exception as e:
        st.error(f"Error configuring API Key: {e}")
        is_model_ready = False
else:
    st.warning("Please enter your API Key in the sidebar to begin.")
    is_model_ready = False


@st.cache_data(show_spinner="Processing your text...")
def call_gemini_api(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


@st.cache_data
def load_data_from_json(json_text):
    if not json_text:
        return pd.DataFrame()
    
    mainverb_text, counterverb_text = json_text.split("==========")
    mainverb_text = mainverb_text.strip()
    counterverb_text = counterverb_text.strip()

    if mainverb_text.startswith('```json'):
        mainverb_text = mainverb_text[7:]
    if mainverb_text.endswith('```'):
        mainverb_text = mainverb_text[:-3]

    if counterverb_text.startswith('```json'):
        counterverb_text = counterverb_text[7:]
    if counterverb_text.endswith('```'):
        counterverb_text = counterverb_text[:-3]
    
    try:
        df_mainverb_data = json.loads(mainverb_text)
        mainverb_data = json_normalize(df_mainverb_data, sep='.')

        df_counterverb_data = json.loads(counterverb_text)
        counterverb_data = json_normalize(df_counterverb_data, sep='.')

        return mainverb_data, counterverb_data
    except json.JSONDecodeError:
        st.error("Error decoding JSON from model response.")
        return pd.DataFrame()


with st.form("user_input"):
    user_text_input = st.text_area("Your text", max_chars=2500, placeholder='Put your Russian text in here! Maximun 2,500 words.').strip()
    st.form_submit_button('Process!')

if is_model_ready and user_text_input:
    prompt = f"""Extract verbs out of the following text and turn them into their infinitive form, make sure to put stress mark on them. Then provide a list using all of those verbs in their infinitive form. Always return the result as 2 JSON array of objects. The first JSON object must have the verb that got extracted from the text as a key which contains the following objects: 'meaning' (in English infinitive form. Provide strictly only the meaning without any other additional information e.g. "verb": "прийти́", "meaning": "to arrive, to come"), 'aspect' (perfective or imperfective), 'counterpart' (their counterpart aspect verb), 'form', 'level' (difficulty of that word using the CEFR A1 to C2 system), and 'examples'. The keys must exactly be the name provided, do not change it. In 'form' must contain objects 'present/future tense', 'past tense', and 'imperative'. In 'present/future tense' must have objects which contain pronouns and inflected present/future tense form according to the pronoun in Russian (if the verb's aspect is imperfective, provide the congujation in present but if the verb's aspect is perfective, provide the conjugation in future. In 'past tense' must have objects which contain gender and number (masc, fem, neu, and pl) and inflected past tense form according to the gender and number in Russian. Lastly, in 'imperative' must have objects which contain two of the possible pronouns(sing and pl you in Russian) and inflected imperative form accordingly. In 'examples' must always contains 3 sentences strictly in 2 lists of strings. The first list is the Russian examples and the second list is the English Translated version. The examples have to show how to use the conjugated form of that verb in a sentence. The key 'verb' MUST NOT have duplicates, if that verb has more than one meaning put them together in the same dictionary inside the key 'meaning', for example, "verb": "прийти́", "meaning": "to arrive, to come". Every 'verb' key MUST be unique. All forms of the verb(present/future, past, and imperative) must be contained witihin these 3 examples. Every single Russian word in the array must have stress mark on them that includes 'e' to 'ё' but except the obvious one like word that has 1 vowel in itself. There MUST NOT be any empty objects in the array. Now, in the second JSON object. The requirement is strictly that same as the first JSON object except that you use the 'counterpart' of the extracted verb as a key of 'verb' instead. Agaian, There MUST NOT be any empty objects in the array.

These are some examples for you so the format will always be consistent:
{{
    "verb": "гляде́ть",
    "meaning": "to look",
    "aspect": "imperfective",
    "counterpart": "погляде́ть",
    "form": {{
      "present/future tense": {{
        "я": "гляжу́",
        "ты": "гляди́шь",
        "он/она/оно": "гляди́т",
        "мы": "гляди́м",
        "вы": "гляди́те",
        "они": "глядя́т"
      }},
      "past tense": {{
        "masc": "гляде́л",
        "fem": "гляде́ла",
        "neu": "гляде́ло",
        "pl": "гляде́ли"
      }},
      "imperative": {{
        "sing": "гляди́",
        "pl": "гляди́те"
      }}
    }},
    "level": "A2",
    "examples": [
      [
        "Я смотрю́ на него́.",
        "Ты смотре́л на карти́ну.",
        "Гляди́те, кака́я краси́вая за́ря!"
      ],
      [
        "I am looking at him.",
        "You were looking at the painting.",
        "Look, what a beautiful sunset!"
      ]
    ]
  }},
  {{
    "verb": "опроки́нуть",
    "meaning": "to overturn",
    "aspect": "perfective",
    "counterpart": "опроки́дывать",
    "form": {{
      "present/future tense": {{
        "я": "опрокину́",
        "ты": "опроки́нешь",
        "он/она/оно": "опроки́нет",
        "мы": "опроки́нем",
        "вы": "опроки́нете",
        "они": "опроки́нут"
      }},
      "past tense": {{
        "masc": "опроки́нул",
        "fem": "опроки́нула",
        "neu": "опроки́нуло",
        "pl": "опроки́нули"
      }},
      "imperative": {{
        "sing": "опроки́нь",
        "pl": "опроки́ньте"
      }}
    }},
    "level": "B2",
    "examples": [
      [
        "Ветéр опроки́нет ло́дку.",
        "Он опроки́нул стол.",
        "Не опроки́ньте ча́шку!"
      ],
      [
        "The wind will overturn the boat.",
        "He overturned the table.",
        "Don't overturn the cup!"
      ]
    ]
  }}

Always seperate 2 json objects with "=========="
JSON object seperation example for consistency:
[
  {{
    "verb": "рабо́тать",
    "meaning": "to work",
    "aspect": "imperfective",
    "counterpart": "порабо́тать",
    "form": {{
      "present/future tense": {{
        "я": "рабо́таю",
        "ты": "рабо́таешь",
        "он/она/оно": "рабо́тает",
        "мы": "рабо́таем",
        "вы": "рабо́таете",
        "они": "рабо́тают"
      }},
      "past tense": {{
        "masc": "рабо́тал",
        "fem": "рабо́тала",
        "neu": "рабо́тало",
        "pl": "рабо́тали"
      }},
      "imperative": {{
        "sing": "рабо́тай",
        "pl": "рабо́тайте"
      }}
    }},
    "level": "A1",
    "examples": [
      [
        "Где ты рабо́таешь сейча́с?",
        "Мы рабо́тали всю но́чь.",
        "Рабо́тайте быстре́е, пожа́луйста!"
      ],
      [
        "Where do you work now?",
        "We worked all night.",
        "Work faster, please!"
      ]
    ]
  }}
]
==========
[
  {{
    "verb": "порабо́тать",
    "meaning": "to work for a while (perfective)",
    "aspect": "perfective",
    "counterpart": "рабо́тать",
    "form": {{
      "present/future tense": {{
        "я": "порабо́таю",
        "ты": "порабо́таешь",
        "он/она/оно": "порабо́тает",
        "мы": "порабо́таем",
        "вы": "порабо́таете",
        "они": "порабо́тают"
      }},
      "past tense": {{
        "masc": "порабо́тал",
        "fem": "порабо́тала",
        "neu": "порабо́тало",
        "pl": "порабо́тали"
      }},
      "imperative": {{
        "sing": "порабо́тай",
        "pl": "порабо́тайте"
      }}
    }},
    "level": "B1",
    "examples": [
      [
        "Они́ порабо́тают в саду́ за́втра.",
        "Я порабо́тал в огоро́де всего́ ча́с.",
        "Порабо́тай немного́, а пото́м отдохни́."
      ],
      [
        "They will work in the garden tomorrow (for a while).",
        "I worked in the garden for only an hour.",
        "Work a little, and then rest."
      ]
    ]
  }}
]

This is the text that you have to work with:
"
{user_text_input}
"


"""

    raw_json_text = call_gemini_api(prompt) 
    
    if raw_json_text:
        df_rus, df_ctrus = load_data_from_json(raw_json_text)


st.divider()


try:
  st.header(f'There are {len(df_rus)} verbs in the text!')
  #List of contents USE popover?
  #Graph for CEFR freq!!

  #MAIN VERB
  # df_rus = df_rus.sort_values(by='level', ascending=False).reset_index() #NOT NOW
  df_rus['verb'] = df_rus['verb'].str.capitalize()
  df_rus['meaning'] = df_rus['meaning'].str.capitalize()
  df_rus['aspect'] = df_rus['aspect'].str.capitalize()
  df_rus['counterpart'] = df_rus['counterpart'].str.capitalize()

  pre_fur_tense_cols = [col for col in df_rus.columns if col.startswith('form.present/future tense.')]
  past_tense_cols = [col for col in df_rus.columns if col.startswith('form.past tense.')]
  imperative_cols = [col for col in df_rus.columns if col.startswith('form.imperative.')]

  #COUNTERPART VERB
  # df_ctrus = df_ctrus.sort_values(by='level', ascending=False).reset_index()
  df_ctrus['verb'] = df_ctrus['verb'].str.capitalize()
  df_ctrus['meaning'] = df_ctrus['meaning'].str.capitalize()
  df_ctrus['aspect'] = df_ctrus['aspect'].str.capitalize()
  df_ctrus['counterpart'] = df_ctrus['counterpart'].str.capitalize()

  ct_pre_fur_tense_cols = [col for col in df_ctrus.columns if col.startswith('form.present/future tense.')]
  ct_past_tense_cols = [col for col in df_ctrus.columns if col.startswith('form.past tense.')]
  ct_imperative_cols = [col for col in df_ctrus.columns if col.startswith('form.imperative.')]

  for i in range(len(df_rus)):
    #MAIN
    verb = df_rus.loc[i, 'verb']
    meaning = df_rus.loc[i, 'meaning']
    if '(' or ')' in meaning:
        meaning = re.sub(r'\s*\([^)]*\)', '', meaning)
    aspect = df_rus.loc[i, 'aspect']
    counterpart = df_rus.loc[i, 'counterpart']
    level = df_rus.loc[i, 'level']

    #PRESENT/FUTURE
    pre_fur_conj = df_rus[pre_fur_tense_cols].iloc[i]
    pre_fur_conj.index = ['я', 'ты','он/она́/оно́', 'мы', 'вы', 'они́']
    pre_fur_conj.index.name = 'Grammar Form'
    pre_fur_conj.name = 'Conjugation'
    pre_fur_conj_df = pre_fur_conj.to_frame()

    #PAST
    past_conj = df_rus[past_tense_cols].iloc[i]
    past_conj.index = ['Masculine (я/ты/он)', 'Feminine (я/ты/она́)', 'Neuter (оно́)', 'Plural (мы/вы/они́)']
    past_conj.index.name = 'Grammar Form'
    past_conj.name = 'Conjugation'
    past_conj_df = past_conj.to_frame()

    #IMPERATIVE
    imperative_conj = df_rus[imperative_cols].iloc[i]
    imperative_conj.index = ['Singular (ты)', 'Plural (вы)']
    imperative_conj.index.name = 'Grammar Form'
    imperative_conj.name = 'Conjugation'
    imperative_conj_df = imperative_conj.to_frame()


    #COUNTERPART
    verb_ct = df_ctrus.loc[i, 'verb']
    meaning_ct = df_ctrus.loc[i, 'meaning']
    if '(' or ')' in meaning_ct:
        meaning_ct = re.sub(r'\s*\([^)]*\)', '', meaning_ct)
    aspect_ct = df_ctrus.loc[i, 'aspect']
    counterpart_ct = df_ctrus.loc[i, 'counterpart']
    level_ct = df_ctrus.loc[i, 'level']

    #PRESENT/FUTURE
    ct_pre_fur_conj = df_ctrus[ct_pre_fur_tense_cols].iloc[i]
    ct_pre_fur_conj.index = ['я', 'ты','он/она́/оно́', 'мы', 'вы', 'они́']
    ct_pre_fur_conj.index.name = 'Grammar Form'
    ct_pre_fur_conj.name = 'Conjugation'
    ct_pre_fur_conj_df = ct_pre_fur_conj.to_frame()

    #PAST
    ct_past_conj = df_ctrus[ct_past_tense_cols].iloc[i]
    ct_past_conj.index = ['Masculine (я/ты/он)', 'Feminine (я/ты/она́)', 'Neuter (оно́)', 'Plural (мы/вы/они́)']
    ct_past_conj.index.name = 'Grammar Form'
    ct_past_conj.name = 'Conjugation'
    ct_past_conj_df = ct_past_conj.to_frame()

    #IMPERATIVE
    ct_imperative_conj = df_ctrus[ct_imperative_cols].iloc[i]
    ct_imperative_conj.index = ['Singular (ты)', 'Plural (вы)']
    ct_imperative_conj.index.name = 'Grammar Form'
    ct_imperative_conj.name = 'Conjugation'
    ct_imperative_conj_df = ct_imperative_conj.to_frame()


    with st.expander(f'**{verb}** -- {meaning} -- {aspect}'):
        tab1, tab2 = st.tabs([verb, counterpart])

        with tab1:
          vocab, lvl_vocab = st.columns([18, 1])
          with vocab:
            st.markdown(f"""<h3>{verb}&ensp;<span style="font-size: 0.5em; background-color: rgba(128, 128, 128, 0.5); padding: 5px; border-radius: 5px;">{aspect}</span><br><span style="color: #E2BD6B; font-size: 1em;">{meaning}</span></h3>""", unsafe_allow_html=True)
          with lvl_vocab:
            st.subheader(f':gray-background[{level}]')

          st.markdown(f"""<h5>The verb's counterpart: <span style="background-color: rgba(185, 132, 219, 0.3); padding: 5px; border-radius: 5px;">{counterpart}</span></h5>""", unsafe_allow_html=True)

          prefur, past, imperative = st.columns(3)
          
          with prefur:
              if aspect == 'Imperfective':
                  st.markdown(f'<h4>Present Tense</h4>', unsafe_allow_html=True)
              elif aspect == 'Perfective':
                  st.markdown(f'<h4>Future Tense</h4>', unsafe_allow_html=True)
              st.dataframe(pre_fur_conj_df)

          with past:
              st.markdown('<h4>Past Tense</h4>', unsafe_allow_html=True)
              st.dataframe(past_conj_df)

          with imperative:
              st.markdown('<h4>Imperative</h4>', unsafe_allow_html=True)
              st.dataframe(imperative_conj_df)

          st.markdown('<h4>Examples</h4>', unsafe_allow_html=True)
          for sen in range(3):
              st.markdown(f"""<span style='color: #B984DB;'>{df_rus.loc[i, 'examples'][0][sen]}<br><span style='color: initial;'>{df_rus.loc[i, 'examples'][1][sen]}</span>""", unsafe_allow_html=True)
        
        with tab2:        
          vocab_ct, lvl_vocab_ct = st.columns([18, 1])
          with vocab_ct:
            st.markdown(f"""<h3>{verb_ct}&ensp;<span style="font-size: 0.5em; background-color: rgba(128, 128, 128, 0.5); padding: 5px; border-radius: 5px;">{aspect_ct}</span><br><span style="color: #E2BD6B; font-size: 1em;">{meaning_ct}</span></h3>""", unsafe_allow_html=True)
          with lvl_vocab_ct:
            st.subheader(f':gray-background[{level_ct}]')

          st.markdown(f"""<h5>The verb's counterpart: <span style="background-color: rgba(185, 132, 219, 0.3); padding: 5px; border-radius: 5px;">{counterpart_ct}</span></h5>""", unsafe_allow_html=True)

          prefur, past, imperative = st.columns(3)
          
          with prefur:
              if aspect == 'Imperfective':
                  st.markdown(f'<h4>Present Tense</h4>', unsafe_allow_html=True)
              elif aspect == 'Perfective':
                  st.markdown(f'<h4>Future Tense</h4>', unsafe_allow_html=True)
              st.dataframe(ct_pre_fur_conj_df)

          with past:
              st.markdown('<h4>Past Tense</h4>', unsafe_allow_html=True)
              st.dataframe(ct_past_conj_df)

          with imperative:
              st.markdown('<h4>Imperative</h4>', unsafe_allow_html=True)
              st.dataframe(ct_imperative_conj_df)

          st.markdown('<h4>Examples</h4>', unsafe_allow_html=True)
          for sen in range(3):
              st.markdown(f"""<span style='color: #B984DB;'>{df_ctrus.loc[i, 'examples'][0][sen]}<br><span style='color: initial;'>{df_ctrus.loc[i, 'examples'][1][sen]}</span>""", unsafe_allow_html=True)
        
except NameError:
    st.warning("No verbs found or processed yet. Please enter text and submit to see results.")

