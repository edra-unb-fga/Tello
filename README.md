# Tello Drone Control com Gestos

## Descrição
Este projeto é uma versão inicial e de teste para controlar o Tello usando gestos. Ele utiliza visão computacional para interpretar gestos da mão e traduzí-los em comandos para o drone.

**Atenção**: Esta versão foi modificada da que testamos, algumas adaptações que não eram para quebrar o código foram feitas mas se não rodar fale comigo que mando a última versão testada 

## Características
- Interface gráfica para ajustar configurações de desempenho e variáveis de missão
- Controle de gestos usando visão computacional
- Overlay de informações no stream de vídeo
- Árvore de comportamento para gerenciar a sequência de ações do drone

## Requisitos
Para executar este projeto, você precisará dos seguintes pacotes Python:

```
djitellopy
opencv-python
mediapipe
py_trees
numpy
```

Você pode instalar todos os requisitos usando o arquivo `requirements.txt` fornecido:

```
pip install -r requirements.txt
```

## Como usar
1. Certifique-se de que seu drone Tello está ligado e conectado à mesma rede Wi-Fi que seu computador.
2. Execute o script principal:
   ```
   python main.py
   ```
3. Use a interface gráfica para ajustar as configurações conforme necessário.
4. Clique no botão "Iniciar Missão" para começar o controle por gestos.

