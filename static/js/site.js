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

    document.getElementById("form-book").addEventListener("change", function(){
        input_chunk_size = document.getElementById("input-chunk-size");
        chunk_size = input_chunk_size.value;
        input_chunk_part = document.getElementById("input-chunk-part");
        max_part = Math.ceil(NDOC/chunk_size);
        if (input_chunk_part.value == max_part && chunk_size != NDOC){
            n_pages = (NDOC % chunk_size) *2;
        }else{
            n_pages = chunk_size * 2;
        }

        input_chunk_part.setAttribute("max",max_part);
        document.getElementById("pages-result").textContent = n_pages;

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

// element.offsetWidth > 0 && element.offsetHeight > 0; // visible
