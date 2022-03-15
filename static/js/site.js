var aLazyLoad = new LazyLoad({
  elements_selector: ".lazy"
});
//callback_enter: entered
function entered(element){
    console.log(element)
    element.parentNode.classList.add("entered");
}

var NDOC = 420;

window.addEventListener("beforeprint", function(event) {
    aLazyLoad.loadAll();
});

function formular(){
    menu = document.getElementById("menu-form");
    intro = document.querySelector(".intro")
    intro.classList.add("not-editing");
    intro.addEventListener("click", function(ev){
        if(intro.classList.contains("editing") && (ev.target.id === "last-element-hidden" || ev.target.parentElement.id === "last-element-hidden" )){
            intro.classList.remove("editing");
            intro.classList.add("not-editing");
        }else{
            intro.classList.add("editing");
            intro.classList.remove("not-editing");
        }
    });

    select_format = document.getElementById("select-format");
    input_width = document.getElementById("input-width");
    input_height = document.getElementById("input-height");

    document.getElementById("select-sort").addEventListener("change", function(e){
      let value = e.target.value
      if(value === "byIndexationDate"){
        sort_books_by_data("data-indexation-date");
      }else if(value === "byAlphabeticalTitle"){
        sort_books_by_data("data-title");
      }
    })

    document.getElementById("form-chunk").addEventListener("change", function(){
      let input_chunk_size = document.getElementById("input-chunk-size");
      let chunk_size = input_chunk_size.value;
      let input_chunk_part = document.getElementById("input-chunk-part");
      let chunk_part = input_chunk_part.value;
      let max_part = Math.ceil(NDOC/chunk_size);
      if (chunk_part == max_part && chunk_size != NDOC){
          n_pages = (NDOC % chunk_size) *2;
      }else{
          n_pages = chunk_size * 2;
      }

      input_chunk_part.setAttribute("max",max_part);
      document.getElementById("pages-result").textContent = n_pages;

      filter_books(chunk_size,chunk_part);
    })

    document.getElementById("form-book").addEventListener("change", function(){
        // selection format
        if (input_width.value == 148 && input_height.value == 210){
            select_format.value = "A5";
        } else if (input_width.value == 152.4 && input_height.value == 228.6){
            select_format.value = "roman";
        } else if (input_width.value == 177.8 && input_height.value == 254){
            select_format.value = "executive";
        } else if (input_width.value == 210 && input_height.value == 297){
            select_format.value = "A4";
        } else if (input_width.value == 215.9 && input_height.value == 279.4){
            select_format.value = "letter";
        } else{
            select_format.value = "custom";
        }

    });
    document.getElementById("select-format").addEventListener("change", function(){
        if (select_format.value == "A5"){
            input_width.value = 148;
            input_height.value = 210;
        } else if (select_format.value == "roman"){
            input_width.value = 152.4;
            input_height.value = 228.6;
        } else if (select_format.value == "executive"){
            input_width.value = 177.8;
            input_height.value = 254;
        } else if (select_format.value == "A4"){
            input_width.value = 210;
            input_height.value = 297;
        } else if (select_format.value == "letter"){
            input_width.value = 215.9;
            input_height.value = 279.4;
        }
    })
}

if(document.getElementsByTagName("form").length > 0){
    formular();
}

pages = document.querySelectorAll(".page")
window.addEventListener("scroll", function(){
  for (var i = 0; i < pages.length; i++) {
    if (document.body.scrollTop + (window.innerHeight/2) < pages[i].getBoundingClientRect().top){
      pages[i].classList.add("above-page");
    }else{
      pages[i].classList.remove("above-page");
    }
  }
});

function sort_books_by_data(attribute) {
    var docs_biblio = document.querySelectorAll(".biblio li");
    var docs_biblio_array = Array.from(docs_biblio);
    let sorted_biblio = docs_biblio_array.sort(function(a, b) {
        return (a.getAttribute(attribute) < b.getAttribute(attribute)) ? -1 : ((a.getAttribute(attribute) > b.getAttribute(attribute)) ? 1 : 0);
    });
    sorted_biblio.forEach(e => document.querySelector(".biblio").appendChild(e));

    var docs_page = document.querySelectorAll(".documents .book");
    console.log(docs_page);
    var docs_page_array = Array.from(docs_page);
    console.log(docs_page_array);
    let sorted_page = docs_page_array.sort(function(a, b) {
      console.log(a.getAttribute(attribute));
        return (a.getAttribute(attribute) < b.getAttribute(attribute)) ? -1 : ((a.getAttribute(attribute) > b.getAttribute(attribute)) ? 1 : 0);
    });
    console.log(sorted_page);
    sorted_page.forEach(e => document.querySelector(".documents").appendChild(e));
}

function filter_books(chunk_size, chunk_part){
  var docs_biblio = document.querySelectorAll(".biblio li");
  var docs_page = document.querySelectorAll(".documents .book");

  console.log(docs_biblio.length);
  console.log(docs_page.length);

  var chunk_start = ((chunk_part-1) * chunk_size)
  var chunk_end = Math.min(chunk_start + chunk_size -1, docs_page.length)

  console.log(chunk_start);
  console.log(chunk_end)
  for (var i = 0; i < docs_page.length; i++) {
    if(i <chunk_start || i > chunk_end){
      docs_biblio[i].classList.add("book_hide");
      docs_page[i].classList.add("book_hide");
    }else{
      docs_biblio[i].classList.remove("book_hide");
      docs_page[i].classList.remove("book_hide");
    }
  }


}

// element.offsetWidth > 0 && element.offsetHeight > 0; // visible
