// créer une worker, récupérer le status régulièrement, recevoir la moyenne en blob, supprimer le worker 
async function generateAverage(group, width, height) {

  return new Promise((resolve, reject) => {

    const worker = new Worker(
      "static/js/lib/average-worker.js",
      {type: "module"}
    );

    worker.onmessage = event => {
      const message = event.data;
      switch (message.type) {
        case "progress":
          document.getElementById("progress").value = message.value;
          document.getElementById("status").textContent = `${message.current} / ${message.total}`;
          break;

        // quand le worker a fini de travaillé
        case "done":
          const blob = new Blob([message.buffer],{type: "image/png"});
          // On détruit le Worker immédiatement, pour faire disparaître toutes les références restantes dans son scop.
          worker.terminate();
          resolve(blob);
          break;

        case "error":
          worker.terminate();
          reject(new Error(message.message));
          break;
      }
    };

    worker.onerror = error => {
      worker.terminate();
      reject(error);
    };
    
    // let's go !
    worker.postMessage({group, width, height,mode:"additive"});
  });
}

// la fonction principale qui est appelée seulement si les images de la couv n'existe pas
// c-a-d pas générées à l'avance et mises en fichier static sur le serveur 
async function generateCoverImages(book, documents, page_width, page_height, scale, static_url){
    document.querySelector("header").style.display = "block";
  
    const width = parseInt(page_width * book.dpi);
    const height = parseInt(page_height * book.dpi);

    const groupA = [];
    for (const doc of documents) {
      const obj = {
        url: static_url + doc.id + "-f" + doc.pages[0].pagination + ".jpg",
        x: parseFloat(doc.pages[0].match.center[0]),
        y: parseFloat(doc.pages[0].match.center[1]),
        scale: parseFloat(scale)
      }
      groupA.push(obj)
    }
    
    const groupB = [];
    for (const doc of documents) {
       const obj = {
        url: static_url + doc.id + ".jpg",
        x: parseFloat(doc.pages[0].match.center[0]),
        y: parseFloat(doc.pages[0].match.center[1]),
        scale: parseFloat(scale)
       }
       groupB.push(obj)
    }

    try {
      /*
       ******************************************************************
       * Première de couverture : les logos
       ******************************************************************
       */
      document.getElementById("step").innerHTML = "Génération de la 1<sup>re</sup> de couverture";
      document.getElementById("progress").value = 0;

      const blobA = await generateAverage(groupA, width, height);

      // display result on page
      const urlA = URL.createObjectURL(blobA);
      document.getElementById("resultA").src = urlA;

      /*
       ******************************************************************
       * 4e de couverture : les couvertures
       ******************************************************************
       */
      
      document.getElementById("step").innerHTML = "Génération de la 4<sup>e</sup> de couverture";
      document.getElementById("progress").value = 0;

      const blobB = await generateAverage(groupB, width, height);

      // display result on page
      const urlB = URL.createObjectURL(blobB);
      document.getElementById("resultB").src = urlB;

      // quand c'est fini on cache le header
      document.getElementById("step").textContent = "Terminé.";
      setTimeout(()=>{
        document.querySelector("header").style.display = "none";
      }, 1000);
      
    } catch (error) {
      console.error(error);
      document.getElementById("status").textContent =
        "Erreur : " + error.message;
    }
}