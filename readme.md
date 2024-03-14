Hola y bienvenidos a tu primer proyecto END tu END como Deita Saiensist

En esta serie de videos, vamos a hacer un dashboard de artículos científicos. Vamos a segmentarlos por Zona geografica si es posible, y por fecha, para intentar ver una evolución histórica de las publicaciones científicas de un tema concreto.

Para este proyecto voy a utilizar K8s, Docker, Post gre esekuele, Strimlit, Paiton y la batería que ya todos conocemos de librerías de DeitaSaiens.

En la primera parte de este proyecto, haremos un escraper de artículos científicos. 

Subdividiremos este subproyecto en los siguientes episodios:

- PARTE 1 Creando el web escraper: En esta parte, primero configuraremos la base de datos, luego, vamos a crear un webscrapper, que va a obtener artículos desde la api de PabMed y los va a complementar la información con la api de CrossREF para sacar información extra.
- PARTE 2 Conectándonos a Postgres: En esta parte, nos enfocaremos puramente en crear las tablas y relaciones necesarias para almacenar y darle sentido a los datos.
- PARTE 3 Creando la imagen de Doquer y el deploy en Cubernetis: donde nos enfocaremos en crear nuestra primera imagen de docker, subirla al container registry de github, hacerla pública y hacer un pull desde k8s. Para enfocarnos puramente en los conceptos básicos de administración con Kiubsitiel, opté por dejar pública la imagen, pero para la siguiente parte, veremos cómo obtener acceso a imágenes privadas.

¡Sin más que decir Comencemos!