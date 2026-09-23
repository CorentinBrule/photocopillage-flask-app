
//callback_enter: entered
function entered(element){
    console.log(element)
    element.parentNode.classList.add("entered");
}

var NDOC = 420;

function formular(){

    document.getElementById("form-book").onkeypress = function(e) {
      var key = e.charCode || e.keyCode || 0;
      if (key == 13 && e.target.type !== "submit") {
        e.preventDefault();
      }
    }

    menu = document.getElementById("form-book");
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

    let label_sort = document.querySelector(".tri");

    document.getElementById("select-sort").addEventListener("change", function(e){
      
      let value = e.target.value
      if(value === "byIndexationDate"){
        label_sort.textContent = "date d’indexation";
        sort_books_by_data("data-indexation-date");
      }else if(value === "byAlphabeticalTitle"){
        label_sort.textContent = "titre des livres";
        sort_books_by_data("data-title");
      }
    })

    document.getElementById("form-chunk").addEventListener("change", function(){
      let input_chunk_size = document.getElementById("input-chunk-size");
      let chunk_size = input_chunk_size.value;
      let input_chunk_part = document.getElementById("input-chunk-part");
      let chunk_part = input_chunk_part.value;
      let max_part = Math.ceil(NDOC/chunk_size);
      let n_pages;
      if (chunk_part == max_part && chunk_size != NDOC){
          n_pages = (NDOC % chunk_size) *2;
      }else{
          n_pages = chunk_size * 2;
      }

      input_chunk_part.setAttribute("max",max_part);
      document.getElementById("pages-result").textContent = n_pages;
      
      var n_start = ""+ (chunk_size*chunk_part-chunk_size+1)
      var n_end = "" + Math.min(chunk_size*chunk_part, NDOC)
      document.querySelector(".interval").textContent =  "000".substring(0, 3 - n_start.length) + n_start + "–" + "000".substring(0,3 - n_end.length) + n_end; 

      filter_books(chunk_size, chunk_part);
      draw_bookbox(input_width.value, input_height.value, n_pages)

    })

    document.getElementById("form-book").addEventListener("change", function(){
        // selection format !!! pas le bon id
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
        change_book_size(input_width.value,input_height.value);
        draw_bookbox(input_width.value,input_height.value, document.getElementById("pages-result").textContent)
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
  document.getElementById("select-scale").addEventListener("change",function(ev){
    document.querySelector(".echelle").textContent = ev.target.options[ev.target.selectedIndex].textContent;
    document.documentElement.style.setProperty('--SCALE', ev.target.value);
  });
}

if(document.getElementsByTagName("form").length > 0){
    formular();
}

apropos = document.getElementById("apropos")

window.addEventListener("scroll", function(){
  if(!apropos.classList.contains("scrolling")){
    if (document.body.scrollTop  > apropos.getBoundingClientRect().bottom){
      apropos.classList.add("apropos-hide");
    }
  }
  
  for (page of document.querySelectorAll(".page")) {
    if (document.body.scrollTop + (window.innerHeight/2) < page.getBoundingClientRect().top){
      page.classList.add("above-page");
    }else{
      page.classList.remove("above-page");
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
        // console.log(a.getAttribute(attribute));
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

function change_book_size(width, height){
  document.documentElement.style.setProperty('--PAGEWIDTH', width+"mm");
  document.documentElement.style.setProperty('--PAGEHEIGHT', height+"mm");
}

/* qu'est-ce que c'est ? */
function calculate_mult(){
  let vh_pixel = window.innerHeight;
  // let dpi = findFirstPositive(x => matchMedia(`(max-resolution: ${x}dpi)`).matches)
  let dpi = 100;
  let max_inch = 12;
  let max_pixel = max_inch * dpi;
  let mult = Math.min(vh_pixel/max_pixel,1);
  document.documentElement.style.setProperty('--MULT', mult);
  return mult;
}

calculate_mult();
window.onresize = function(){
  calculate_mult();
}

function findFirstPositive (f,b=1,d=(e,g,c)=>g<e?-1:0<f(c=e+g>>>1)?c==e||0>=f(c-1)?c:d(e,c-1):d(c+1,g)) {
  for (;0>=f(b);b<<=1);return d(b>>>1,b)|0
}


function draw_bookbox(width,height,npages){
  const bookbox = document.querySelector(".bookbox");
  bookbox.style.setProperty('--width', width+"px");
  bookbox.style.setProperty('--height', height+"px");
  bookbox.style.setProperty('--depth', npages/15+"px");
  bookbox.style.setProperty('--npage', npages);
}

draw_bookbox(document.querySelector("#input-width").value,document.querySelector("#input-height").value, document.querySelector("#pages-result").textContent)

document.querySelector("#apropos-toggle").onclick = ()=>{
  if(apropos.classList.contains("apropos-hide")){
    apropos.classList.add("scrolling")
    setTimeout(()=>{
      apropos.scrollIntoView({ behavior: "smooth"});
    },200)
    setTimeout(()=>{
      apropos.classList.remove("scrolling")
    },1000)
    
  }else{
    // location.hash = "";
  }
  document.querySelector(".apropos").classList.toggle("apropos-hide")
}

// element.offsetWidth > 0 && element.offsetHeight > 0; // visible
