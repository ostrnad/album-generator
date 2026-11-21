/* ── Einbettung: eingebettete Bilder und Kacheln per id finden (ARCHITEKTUR.md 3.4) ──
   Die Daten einer Component verweisen nur per id auf Bilddaten. Dahinter steht entweder
   - ein <img> der Grundansicht (Bild liegt schon als Data-URL vor) oder
   - ein <script type="application/octet-stream" data-typ="image/jpeg" id="…"> mit Base64-Inhalt.
   Wird von jeder Component benutzt, die eingebettete Bilder braucht; auf fremden Seiten mit einbinden. */
(function(){
"use strict";
if(window.AlbumEinbettung)return;
var urls={};

/* Liefert eine URL, die man einem <img> oder einer Textur geben kann, oder null. */
function bildUrl(id){
  if(urls[id])return urls[id];
  var el=document.getElementById(id);
  if(!el)return null;
  if(el.tagName==="IMG")return el.currentSrc||el.src;
  if(el.tagName!=="SCRIPT")return null;
  var b64=el.textContent.replace(/\s+/g,""),bin=atob(b64),n=bin.length,bytes=new Uint8Array(n);
  for(var i=0;i<n;i++)bytes[i]=bin.charCodeAt(i);
  urls[id]=URL.createObjectURL(new Blob([bytes],{type:el.getAttribute("data-typ")||"application/octet-stream"}));
  return urls[id];
}

/* Gibt eine mit bildUrl erzeugte URL wieder frei (z. B. wenn eine Component ihr Bild nicht mehr braucht). */
function freigeben(id){
  if(urls[id]){URL.revokeObjectURL(urls[id]);delete urls[id]}
}

window.AlbumEinbettung={bildUrl:bildUrl,freigeben:freigeben};
})();
