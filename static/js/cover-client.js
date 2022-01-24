function generateCoverImages(book,documents,page_width,page_height, static_url) {
    console.log(book);
    console.log(documents);
    document.querySelector("header").style.display = "block";
    document.querySelector("#total").innerText = documents.length;
    var canvas_cover = document.createElement('canvas');
    var canvas_logo = document.createElement("canvas");
    image_width_px = parseInt(page_width * book.dpi);
    image_height_px = parseInt(page_height * book.dpi);
    console.log(image_width_px);
    console.log(image_height_px);
    canvas_logo.width = image_width_px;
    canvas_logo.height = image_height_px;
    canvas_cover.width = image_width_px;
    canvas_cover.height = image_height_px;

    let el_logo = document.querySelector(".cover1 img");
    let el_cover = document.querySelector(".cover4 img");

    let ctx_logo =  canvas_logo.getContext("2d");
    let ctx_cover = canvas_cover.getContext("2d");

    for (var i = 0; i < documents.length; i++) {
      // console.log(documents[i].id);
      // documents[i]
      let alpha = 1/(i+1) * 1;

      let img_width = documents[i].pages[0].size.width;
      let img_height = documents[i].pages[0].size.height;
      let x = documents[i].pages[0].match.center[0];
      let y = documents[i].pages[0].match.center[1];
      // console.log(image_width_px/2 - documents[i].pages[0].match.center[0]);
      // console.log(img_width);
      // console.log(img_height);

      let tmp_img_logo = new Image();
      tmp_img_logo._id = documents[i].id;
      tmp_img_logo._w = img_width;
      tmp_img_logo._h = img_height;
      tmp_img_logo._x = image_width_px/2 - documents[i].pages[0].match.center[0];
      tmp_img_logo._y = image_height_px/2 - documents[i].pages[0].match.center[1];
      tmp_img_logo._a = alpha;
      tmp_img_logo.onload = function(){
        // console.log(this._id);
        // console.log(this._w);
        ctx_logo.globalAlpha = this._a;
        ctx_logo.drawImage(this,this._x,this._y,this._w,this._h);
        el_logo.src = canvas_logo.toDataURL();
      }
      tmp_img_logo.src = static_url + documents[i].id + "-f" + documents[i].pages[0].pagination + ".jpg";


      let tmp_img_cover = new Image();
      tmp_img_cover._w = img_width;
      tmp_img_cover._h = img_height;
      tmp_img_cover._x = image_width_px/2 - documents[i].pages[0].match.center[0];
      tmp_img_cover._y = image_height_px/2 - documents[i].pages[0].match.center[1];
      tmp_img_cover._a = alpha;
      tmp_img_cover.onload = function(){
        // console.log(this._w);
        // console.log(this._h);
        // console.log(this._a);
        ctx_cover.globalAlpha = this._a;
        ctx_cover.drawImage(this,this._x,this._y,this._w,this._h);
        el_cover.src = canvas_cover.toDataURL();
        document.querySelector("#step").innerText = i;
        if(i==documents.length-1){
          document.querySelector("header").style.display = "none";
        }
      }
      tmp_img_cover.src = static_url + documents[i].id + ".jpg";
      // img_cover = (url)

    }
    document.querySelector(".cover1").appendChild(canvas_logo);
    document.querySelector(".cover4").appendChild(canvas_cover);
}
