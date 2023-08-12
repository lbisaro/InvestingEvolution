# Configura el logging
def send(msg):
    with open('bot_klines.log', 'a') as f:
        f.write(msg+'\n')
    print(msg)
