from random import random, randrange
import speech_recognition as sr
from nltk import word_tokenize, corpus
import json

LANGUAGE_CORPUS = 'portuguese'
LANGUAGE_SPEAK =  'pt-BR'
CONFIG_PATH = 'config.json'
ANIME_DATA = 'anime_data.json'
ANIME_TOPICS = 'anime_topics.json'


def start():
    global recognizer
    global stop_words
    global assistant_name
    global actions
    
    recognizer = sr.Recognizer()
    stop_words = set(corpus.stopwords.words(LANGUAGE_CORPUS))
    
    # Palavras que eu precisarei resgatar, não podendo ser consideradas
    # como palavras de parada.
    stop_words.remove('mais')
    stop_words.remove('qual')
    
    # Configurações
    with open(CONFIG_PATH, 'r', encoding='UTF8') as config_file:
        settings = json.load(config_file)
        
        assistant_name = settings['name']
        actions = settings['actions']
        
        config_file.close()
        

# Função para escutar os comandos
def listen_command():
    global recognizer
    
    command = None
    
    with sr.Microphone() as sound_source:
        recognizer.adjust_for_ambient_noise(sound_source)
        
        print('\nQual informação você está procurando?')
        speech = recognizer.listen(sound_source, timeout=5, phrase_time_limit=5)
        try:
            command = recognizer.recognize_google(speech, language=LANGUAGE_SPEAK)
        except sr.UnknownValueError:
            pass
        
    return command


# Função para remover as palavras de parada
def cut_stop_words(tokens):
    global stop_words
    
    filtered_tokens = []
    for token in tokens:
        if token not in stop_words:
            filtered_tokens.append(token)
            
    return filtered_tokens


# Função para verificar se o item, informado pelo usuário,
# possui gradações (mais, menos).
def has_gradations(action, item):
    global actions
    
    for a in actions:
        # Se a ação existir na lista de ações...
        if action == a['prefix']:
            for i in a['items']:
                # Se o item existir naquela ação...
                if item == i['name']:
                    # Se aquele item possui gradações...
                    if i['gradations']:
                        return True
            
    return False;            
        

# Função para tokenizar a frase dita pelo usuário.
def tokenize_command(command):
    global assistant_name
    
    action = None
    item = None
    option_chose = None
    gradation = None
    
    tokens = word_tokenize(command, LANGUAGE_CORPUS)
    if tokens:
        tokens = cut_stop_words(tokens)
        
        try:
            if len(tokens) >= 3:
                if assistant_name == tokens[0].lower():                
                    action = tokens[1].lower()
                    item = tokens[2].lower()
                    # Se o item possuir gradações, então o terceiro token será uma gradação. 
                    if has_gradations(action, item):
                        gradation = tokens[3]
                        option_chose = tokens[4].lower()
                    # Caso contrário, o terceiro token será uma opção.                    
                    else:                                    
                        option_chose = tokens[3].lower()
        except:
            pass
                    
    return action, item, option_chose, gradation                    


# Função para retornar o item solicitado pelo usuário.
def return_item(gradation, item_type):
    item = None
    match gradation:
        case 'mais':
            if item_type == 'anime':
                # Abre o arquivo com os dados de cada anime...
                with open(ANIME_DATA, 'r', encoding='UTF8') as anime_file:
                    animes = json.load(anime_file)
                    
                    # Variável pra armazenar o anime mais popular.
                    most_popular = {
                        "name": None,
                        "count_topics": 0
                    }
                    
                    # Percorre todos os animes e encontra o que possui a maior quantidade de tópicos.
                    for anime in animes:
                        if anime['count_topics'] > most_popular['count_topics']:
                            most_popular = anime
                            
                    item = most_popular
                    anime_file.close()
                            
        case 'menos':            
            if item_type == 'anime':
                # Abre o arquivo com os dados de cada anime...
                with open(ANIME_DATA, 'r', encoding='UTF8') as anime_file:
                    animes = json.load(anime_file)
                    
                    # Variável pra armazenar o anime menos popular (começando pelo primeiro anime).
                    less_popular = animes[0]
                    
                    # Percorre todos os animes e encontra o que possui a menor quantidade de tópicos.
                    for anime in animes:
                        if anime['count_topics'] < less_popular['count_topics']:
                            less_popular = anime
                            
                    item = less_popular
                    anime_file.close()
                    
    return item     
               

# Função para retornar um item aleatório.            
def random_item(item_type):
    item = None
    match item_type:
        case 'tópico':
            # Abre o arquivo com os tópicos de cada anime...            
            with open(ANIME_TOPICS, 'r', encoding='UTF8') as anime_topics_file:
                # Gera um dois valores pseudo-aleatórios.
                anime_id = randrange(20)+1
                topic_id = randrange(6)+1
                
                # Resgata o tópico referente aos inteiros gerados anteriormente.
                topics = json.load(anime_topics_file)
                for topic in topics:
                    if topic['animeId'] == anime_id and topic['id'] == topic_id:
                        item = topic
                        break
                
    return item               
            
            

# Função auxiliar que exibe define 'rotas' pra cada comando e imprime o resultado.
def execute_command(action, item, option_chose, gradation):
    match action:
        case 'qual':
            result = return_item(gradation, item)
            if gradation == 'mais':
                print("O anime mais popular é " + result['title'] + " com " + str(result['count_topics']) + " tópicos.")
            elif gradation == 'menos':
                print("O anime menos popular é " + result['title'] + " com " + str(result['count_topics']) + " tópicos.")
            
        case 'indique':
            result = random_item(item)
            print("Encontrei um tópico para você!")         
            print("\nTítulo: " + result['title'])
            print("\nDescrição: " + result['description'])
            print("\nAutor: " + result['author'])
            for d in result['discussion']:
                print('\nComentário: ' + d['text'])
                print('Autor: ' + d['author'])
                
            return False
        

# Função para validar os comandos informados pelo usuário.
def validate_command(action, item, option_chose, gradation):
    global actions
    
    valid = False
    
    # Se os três tokens obrigatóiro foram informados...
    if action and item and option_chose:
        for a in actions:
            # Se a ação existe na lista de ações...
            if action == a['prefix']:
                for i in a['items']:
                    # Se o item existe naquela ação...
                    if item == i['name']:
                        # Se uma gradação foi informada (ela depende do tipo de item)...
                        if gradation:
                            # Se a gradação existir naquele item...
                            if gradation in i['gradations']:
                                # Se a opção existir naquele item...
                                if option_chose in i['options']:
                                    return True                        
                        # Se uma gradação NÃO foi informada...
                        else:
                            # Se a opção existir naquele item...
                            if option_chose in i['options']:
                                return True
                        
                        break
                                   
                                
    return valid
            
        
if __name__ == '__main__':
    start()
    
    continue_loop = True
    while continue_loop:
        try:
            command = listen_command()
            print(f'\nVocê disse: {command}')    
            
            if command:    
                action, item, option_chose, gradation = tokenize_command(command)
                valid = validate_command(action, item, option_chose, gradation)
                if valid:
                    continue_loop = execute_command(action, item, option_chose, gradation)                        
            
        except KeyboardInterrupt:
            print('\nAté a próxima!')
            
            continue_loop = False