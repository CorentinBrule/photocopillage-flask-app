

function biblio(){
    var biblio = document.querySelector(".biblio");
    check_biblio(biblio);
}

function check_biblio(biblio){
    var biblio_limit = biblio.offsetWidth;
    var docs = biblio.querySelectorAll(".doc");
    var next_biblio = document.createElement("ol");
    for (var i = 0 ; i < docs.length ; i++){
        var doc = docs[i];
        /*console.log(doc.offsetLeft)*/
        if( doc.offsetLeft >= biblio_limit ){
            next_biblio.appendChild(doc);
            /*console.log(doc)*/
        }else{
            /*console.log(doc)*/
        }
    }
    if(next_biblio.children.length > 0){
        var next_page = document.createElement("div");
        next_page.className = "page seuil";
        next_biblio.className = "biblio";
        next_page.appendChild(next_biblio);
        var last_page = biblio.parentNode;
        last_page.parentNode.insertBefore(next_page, last_page.nextSibling);
        check_biblio(next_biblio);
    }
}

function seuil(){
    var seuil_pages = document.querySelectorAll(".seuil");
    if (seuil_pages.length%2 == 0){
        var new_page = document.createElement("div");
        new_page.className = "page seuil";
        var last_page = seuil_pages[seuil_pages.length-1]
        last_page.parentNode.insertBefore(new_page, last_page.nextSibling);

    }
}


biblio();
seuil();