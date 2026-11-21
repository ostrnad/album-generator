/* ── <album-panorama>: zylindrisches Panorama per WebGL entzerrt (geradlinig) anzeigen, schwenkbar ──
   Beschreibung: PANORAMA.md, Architektur: ARCHITEKTUR.md.

   Eingabe:  element.daten = {version: 1, bild: "<id>", breite: <px>, hoehe: <px>, bildwinkel: <Grad>}
             bild verweist per id auf das Panorama in voller Auflösung (AlbumEinbettung, einbettung.js).
   Inhalt:   Ein <img> als Kind des Elements ist die Ansicht ohne JavaScript oder WebGL (flacher Streifen).
             Sobald das Widget läuft, ersetzt sein Shadow DOM diese Ansicht.
   Aussehen: Farben über die CSS-Variablen --nav-bg, --nav-shadow (und color); Schrift über
             --album-schrift (Standard: die Schrift der Seite).
   Ereignisse: keine. */
(function(){
"use strict";
if(!window.customElements||customElements.get("album-panorama"))return;

var VS="attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
var FS="precision highp float;uniform sampler2D t;uniform vec2 res;uniform float yaw,pitch,tanv,theta,tanp,rund;"+
"void main(){vec2 p=gl_FragCoord.xy/res*2.-1.;vec3 d=vec3(p.x*tanv*res.x/res.y,p.y*tanv,1.);"+
"float c=cos(pitch),s=sin(pitch);d=vec3(d.x,d.y*c+d.z*s,d.z*c-d.y*s);"+
"float u=(atan(d.x,d.z)+yaw)/theta+.5;if(rund>.5)u=fract(u);"+
"gl_FragColor=texture2D(t,vec2(u,.5-d.y/length(d.xz)/(2.*tanp)));}";
var SVG='<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">';
var CSS=":host{display:block;position:relative;overflow:hidden;font-family:var(--album-schrift,inherit)}"+
":host([aktiv]){aspect-ratio:2.2}"+
"canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none;cursor:grab;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}"+
"canvas.zieht{cursor:grabbing}"+
"button{font:inherit;color:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent}"+
"button:focus-visible{outline:2px solid currentColor;outline-offset:3px}"+
".zoom{position:absolute;right:12px;bottom:12px;display:flex;gap:8px}"+
".zoom button{width:44px;height:44px;display:flex;align-items:center;justify-content:center;background:var(--nav-bg);box-shadow:var(--nav-shadow);border:none;border-radius:999px;padding:0}"+
".zoom button[disabled]{opacity:.35;cursor:default}"+
".hinweis{position:absolute;left:12px;bottom:12px;height:44px;display:flex;align-items:center;gap:8px;font-size:14px;background:var(--nav-bg);box-shadow:var(--nav-shadow);padding:0 16px;border-radius:999px;pointer-events:none;transition:opacity .4s}"+
".hinweis.weg{opacity:0}"+
"@media (max-width:700px){:host([aktiv]){aspect-ratio:1.4}.hinweis{font-size:13px;padding:0 12px}}";

class AlbumPanorama extends HTMLElement{
  constructor(){
    super();
    this._daten=null;this._gestartet=false;
    /* Solange das Widget nicht läuft, zeigt der Slot den flachen Streifen aus dem Element. */
    this.attachShadow({mode:"open"}).innerHTML="<style>"+CSS+"</style><slot></slot>";
  }
  get daten(){return this._daten}
  set daten(d){this._daten=d;this._vorbereiten()}
  connectedCallback(){
    /* Eigenschaft, die vor dem Laden dieser Datei gesetzt wurde, übernehmen */
    if(Object.prototype.hasOwnProperty.call(this,"daten")){var d=this.daten;delete this.daten;this.daten=d}
    this._vorbereiten();
  }
  _vorbereiten(){
    if(this._wartet||this._gestartet||!this._daten||!this.isConnected)return;
    this._wartet=true;
    var el=this;
    /* erst starten, wenn das Panorama in die Nähe des Sichtbereichs kommt */
    if(window.IntersectionObserver){
      var io=new IntersectionObserver(function(es){
        if(es.some(function(e){return e.isIntersecting})){io.disconnect();el._laden()}
      },{rootMargin:"600px 0px"});
      io.observe(this);
    }else this._laden();
  }
  _laden(){
    var el=this,d=this._daten,url=window.AlbumEinbettung&&AlbumEinbettung.bildUrl(d.bild);
    if(!url)return; /* ohne Bilddaten bleibt das flache Bild stehen */
    var img=new Image();
    img.onload=function(){if(el._gestartet)return;el._gestartet=true;try{starten(el,img,d)}catch(e){}};
    img.src=url;
  }
}

function starten(host,img,daten){
  var W=img.naturalWidth,H=img.naturalHeight;if(!W||!H)return;
  var cv=document.createElement("canvas"),gl=null,zwei=false,U={},bereit=false;
  try{gl=cv.getContext("webgl2");zwei=!!gl;if(!gl)gl=cv.getContext("webgl")||cv.getContext("experimental-webgl")}catch(e){}
  if(!gl)return; /* ohne WebGL bleibt das flache Bild stehen */

  /* Programm und Textur anlegen; läuft beim Start und nach jedem wiederhergestellten Grafikkontext */
  function aufbauen(){
    bereit=false;
    function shader(typ,src){var s=gl.createShader(typ);gl.shaderSource(s,src);gl.compileShader(s);return s}
    var pr=gl.createProgram();gl.attachShader(pr,shader(gl.VERTEX_SHADER,VS));gl.attachShader(pr,shader(gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr,gl.LINK_STATUS))return false;
    gl.useProgram(pr);
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
    var a=gl.getAttribLocation(pr,"a");gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
    /* Textur: bei Bedarf auf die Grenze der Grafikkarte verkleinern */
    var max=gl.getParameter(gl.MAX_TEXTURE_SIZE),quelle=img;
    if(W>max){var k=document.createElement("canvas");k.width=max;k.height=Math.max(1,Math.round(H*max/W));k.getContext("2d").drawImage(img,0,0,k.width,k.height);quelle=k}
    gl.bindTexture(gl.TEXTURE_2D,gl.createTexture());
    try{gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,quelle)}catch(e){return false}
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    if(zwei){gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR)}
    else gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
    ["res","yaw","pitch","tanv","theta","tanp","rund"].forEach(function(n){U[n]=gl.getUniformLocation(pr,n)});
    bereit=true;return true;
  }
  if(!aufbauen())return;

  /* Geometrie: Zylinderprojektion, Breite = f*theta, Höhe = 2*f*tan(Bildwinkel/2) */
  var pv=(parseFloat(daten.bildwinkel)||54)*Math.PI/180,tanp=Math.tan(pv/2);
  var theta=W/H*2*tanp,rund=theta>=2*Math.PI-.02;if(theta>2*Math.PI)theta=2*Math.PI;
  var yaw=0,pitch=0,zoom=1,zoomMin=1,ZOOM_MAX=4,bw=1,bh=1;

  /* Shadow DOM: Streifen (Slot) durch Fläche und Bedienelemente ersetzen */
  var sr=host.shadowRoot,slot=sr.querySelector("slot");if(slot)slot.remove();
  sr.appendChild(cv);
  var zb=document.createElement("div");zb.className="zoom";
  zb.innerHTML='<button type="button" aria-label="Verkleinern">'+SVG+'<path d="M5 12h14"/></svg></button><button type="button" aria-label="Vergrößern">'+SVG+'<path d="M5 12h14M12 5v14"/></svg></button>';
  var hinweis=document.createElement("div");hinweis.className="hinweis";
  hinweis.innerHTML=SVG+'<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M3 12h18"/></svg><span>Ziehen zum Umsehen</span>';
  sr.appendChild(hinweis);sr.appendChild(zb);host.setAttribute("aktiv","");
  var minus=zb.children[0],plus=zb.children[1];

  function grenzen(){
    var asp=bw/bh;
    zoomMin=1;if(!rund&&theta<Math.PI){zoomMin=Math.max(1,asp*tanp/Math.tan(theta/2))}
    zoom=Math.min(ZOOM_MAX,Math.max(zoomMin,zoom));
    var tv=tanp/zoom,pl=Math.max(0,pv/2-Math.atan(tv));pitch=Math.min(pl,Math.max(-pl,pitch));
    if(!rund){
      var x=tv*asp,c=Math.cos(pitch),s=Math.abs(Math.sin(pitch)),n=c-tv*s;
      var halb=n>1e-3?Math.atan(x/n):Math.PI/2,yl=Math.max(0,theta/2-halb);
      yaw=Math.min(yl,Math.max(-yl,yaw));
    }
    minus.disabled=zoom<=zoomMin+1e-6;plus.disabled=zoom>=ZOOM_MAX-1e-6;
    return tv;
  }
  function zeichne(){
    var r=host.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
    bw=Math.max(1,r.width);bh=Math.max(1,r.height);
    var w=Math.round(bw*dpr),h=Math.round(bh*dpr);
    if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h}
    var tv=grenzen();
    if(!bereit||gl.isContextLost())return;
    gl.viewport(0,0,w,h);
    gl.uniform2f(U.res,w,h);gl.uniform1f(U.yaw,yaw);gl.uniform1f(U.pitch,pitch);gl.uniform1f(U.tanv,tv);
    gl.uniform1f(U.theta,theta);gl.uniform1f(U.tanp,tanp);gl.uniform1f(U.rund,rund?1:0);
    gl.drawArrays(gl.TRIANGLES,0,3);
  }
  var wartet=false;function neu(){if(wartet)return;wartet=true;requestAnimationFrame(function(){wartet=false;zeichne()})}

  function schwenken(dx,dy){
    var tv=tanp/zoom;
    yaw-=dx*2*tv*(bw/bh)/bw;
    pitch+=dy*2*tv/bh; /* bleibt durch grenzen() im Bild; unvergrößert ist kein Nicken möglich */
    neu();
  }

  /* Maus und Stift: Ziehen schwenkt und neigt */
  var maus=null;
  cv.addEventListener("pointerdown",function(e){
    if(e.pointerType==="touch")return; /* Finger: siehe Touch-Ereignisse unten */
    maus={id:e.pointerId,x:e.clientX,y:e.clientY};
    cv.classList.add("zieht");hinweis.classList.add("weg");try{cv.setPointerCapture(e.pointerId)}catch(x){}
  });
  cv.addEventListener("pointermove",function(e){
    if(!maus||e.pointerId!==maus.id)return;
    var dx=e.clientX-maus.x,dy=e.clientY-maus.y;maus.x=e.clientX;maus.y=e.clientY;schwenken(dx,dy);
  });
  function mausEnde(e){if(maus&&e.pointerId===maus.id){maus=null;cv.classList.remove("zieht")}}
  cv.addEventListener("pointerup",mausEnde);cv.addEventListener("pointercancel",mausEnde);

  /* Finger: Das Panorama nimmt alle Touch-Gesten selbst entgegen (touch-action: none) und entscheidet selbst,
     ob eine Geste schwenkt oder die Seite scrollt. Überlässt man das dem Browser (touch-action: pan-y),
     übernimmt Safari (iOS) Gesten, die auch nur leicht senkrecht beginnen oder werden, und das Schwenken hakt.
     - Unvergrößert entscheidet die Bewegung der ersten SCHWELLE Pixel: waagerecht -> die ganze Geste schwenkt,
       auch nach einem Richtungswechsel; senkrecht -> die Geste scrollt die Seite (mit Nachlauf).
     - Vergrößert schwenkt und neigt jede Geste. Zwei Finger zoomen.
     Nach dem Loslassen laufen Schwenken, Neigen und Scrollen mit abnehmender Geschwindigkeit nach. */
  var SCHWELLE=8,finger=null,nachlauf=0; /* finger: {modus: null|"panorama"|"seite"|"zoom", x, y, sx, sy, abstand, spur} */
  function fingerAbstand(t){return Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY)}
  function gezoomt(){return zoom>zoomMin+1e-6}
  function einFinger(t,modus){return {modus:modus,x:t.clientX,y:t.clientY,sx:t.clientX,sy:t.clientY,spur:[]}}
  cv.addEventListener("touchstart",function(e){
    hinweis.classList.add("weg");
    if(nachlauf){cancelAnimationFrame(nachlauf);nachlauf=0}
    var t=e.touches;
    if(t.length>=2){finger={modus:"zoom",abstand:fingerAbstand(t)};return}
    finger=einFinger(t[0],gezoomt()?"panorama":null);
  });
  cv.addEventListener("touchmove",function(e){
    if(e.cancelable)e.preventDefault(); /* für Browser ohne touch-action */
    if(!finger)return;
    var t=e.touches;
    if(t.length>=2){
      var d=fingerAbstand(t);if(finger.modus==="zoom"&&finger.abstand>0&&d>0)zoom*=d/finger.abstand;
      finger={modus:"zoom",abstand:d};neu();return;
    }
    if(finger.modus==="zoom")return;
    var x=t[0].clientX,y=t[0].clientY;
    if(finger.modus===null){
      var gx=x-finger.sx,gy=y-finger.sy;
      if(Math.max(Math.abs(gx),Math.abs(gy))<SCHWELLE)return; /* noch nicht entschieden */
      finger.modus=Math.abs(gx)>=Math.abs(gy)?"panorama":"seite";
    }
    var dx=x-finger.x,dy=y-finger.y;finger.x=x;finger.y=y;
    var jetzt=performance.now();finger.spur.push([jetzt,dx,dy]);
    while(finger.spur.length&&jetzt-finger.spur[0][0]>100)finger.spur.shift();
    if(finger.modus==="panorama")schwenken(dx,gezoomt()?dy:0);
    else window.scrollBy(0,-dy);
  },{passive:false});
  /* Geschwindigkeit (px/ms) aus den Bewegungen der letzten 100 ms; null, wenn der Finger zuletzt stillstand */
  function tempo(spur){
    if(spur.length<2||performance.now()-spur[spur.length-1][0]>60)return null;
    var dauer=spur[spur.length-1][0]-spur[0][0],wx=0,wy=0;
    for(var i=1;i<spur.length;i++){wx+=spur[i][1];wy+=spur[i][2]}
    return dauer>0?{x:wx/dauer,y:wy/dauer}:null;
  }
  /* Nachlauf: mit der Geschwindigkeit beim Loslassen weiter, dann gleichmäßig abbremsen.
     schritt(dx,dy) bewegt und meldet false, wenn es nicht weitergeht (z. B. am Bildrand). */
  function nachlaufen(v,reibung,schritt){
    if(!v)return;
    var zuletzt=performance.now();
    function weiter(jetzt){
      var dt=Math.min(32,jetzt-zuletzt);zuletzt=jetzt;
      var geht=schritt(v.x*dt,v.y*dt),f=Math.pow(reibung,dt);v.x*=f;v.y*=f;
      nachlauf=geht&&Math.max(Math.abs(v.x),Math.abs(v.y))>.02?requestAnimationFrame(weiter):0;
    }
    nachlauf=requestAnimationFrame(weiter);
  }
  function panoramaNachlauf(spur){
    var v=tempo(spur);if(!v)return;
    if(!gezoomt())v.y=0;
    nachlaufen(v,.996,function(dx,dy){
      var ay=yaw,ap=pitch,tv=tanp/zoom;
      yaw-=dx*2*tv*(bw/bh)/bw;pitch+=dy*2*tv/bh;zeichne();
      if(Math.abs(yaw-ay)<1e-7)v.x=0; /* Bildrand erreicht: in dieser Richtung anhalten */
      if(Math.abs(pitch-ap)<1e-7)v.y=0;
      return v.x!==0||v.y!==0;
    });
  }
  function scrollNachlauf(spur){
    var v=tempo(spur);if(!v)return;v.x=0;
    nachlaufen(v,.997,function(dx,dy){var a=window.scrollY;window.scrollBy(0,-dy);return Math.abs(dy)<.5||window.scrollY!==a});
  }
  function fingerEnde(e){
    var t=e.touches;
    if(!t.length){
      if(finger&&finger.modus==="seite")scrollNachlauf(finger.spur);
      else if(finger&&finger.modus==="panorama")panoramaNachlauf(finger.spur);
      finger=null;return;
    }
    /* nach dem Zoomen mit dem verbliebenen Finger weiter schwenken */
    if(t.length===1)finger=einFinger(t[0],"panorama");
  }
  cv.addEventListener("touchend",fingerEnde);cv.addEventListener("touchcancel",fingerEnde);
  /* Safari: eigene Zoomgeste der Seite auf dem Panorama unterdrücken */
  cv.addEventListener("gesturestart",function(e){e.preventDefault()});
  cv.addEventListener("dblclick",function(){zoom=zoom>zoomMin*1.2?zoomMin:zoomMin*2;neu()});
  plus.addEventListener("click",function(){zoom*=1.5;neu()});
  minus.addEventListener("click",function(){zoom/=1.5;neu()});

  /* Grafikkontext: Verlust abfangen und neu aufbauen (am Handy bei Speicherdruck üblich) */
  cv.addEventListener("webglcontextlost",function(e){e.preventDefault();bereit=false});
  cv.addEventListener("webglcontextrestored",function(){if(aufbauen())zeichne()});
  /* Browser erlauben nur wenige WebGL-Flächen gleichzeitig: außerhalb des Sichtbereichs freigeben */
  var ext=gl.getExtension("WEBGL_lose_context");
  if(ext&&window.IntersectionObserver){
    new IntersectionObserver(function(es){
      var sichtbar=es[es.length-1].isIntersecting;
      try{if(sichtbar&&gl.isContextLost())ext.restoreContext();else if(!sichtbar&&!gl.isContextLost())ext.loseContext()}catch(e){}
    },{rootMargin:"600px 0px"}).observe(host);
  }
  if(window.ResizeObserver)new ResizeObserver(neu).observe(host);else window.addEventListener("resize",neu);
  zeichne();
}

customElements.define("album-panorama",AlbumPanorama);
})();
