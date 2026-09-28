
const S={options:null,mountains:[]};
const $=id=>document.getElementById(id);

function ymd(d){return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function parseDate(s){const a=s.split("-").map(Number);return new Date(a[0],a[1]-1,a[2]);}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x;}
function esc(v){return String(v==null?"":v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
function setOpts(el,items,vk,lk){
  vk=vk||"value";lk=lk||"label";el.innerHTML="";
  items.forEach(x=>{const o=document.createElement("option");if(typeof x==="string"){o.value=x;o.textContent=x;}else{o.value=x[vk];o.textContent=x[lk];}el.appendChild(o);});
}
function currentMountain(){const id=Number($("mountainSelect").value);return S.mountains.find(x=>x.id===id)||S.mountains[0];}

function populateHours(){
  const host=$("hourControls");
  S.options.hours.forEach(x=>{
    const l=document.createElement("label");
    l.innerHTML='<input class="hour-check" type="checkbox" value="'+x.hour+'" checked>'+esc(x.label);
    host.appendChild(l);
  });
  $("allHours").onchange=e=>document.querySelectorAll(".hour-check").forEach(x=>x.checked=e.target.checked);
  host.onchange=e=>{
    if(!e.target.classList.contains("hour-check"))return;
    const a=[...document.querySelectorAll(".hour-check")];
    $("allHours").checked=a.every(x=>x.checked);
  };
}
function populateMonths(){
  $("monthGrid").innerHTML=["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    .map(x=>'<label><input class="month-check" type="checkbox" value="'+x+'">'+x+'月</label>').join("");
}
function populateTrigrams(){
  const m=new Map();
  S.mountains.forEach(x=>{if(!m.has(x.trigram_id))m.set(x.trigram_id,{value:x.trigram_id,label:"【"+x.direction.slice(0,2)+"】"+x.trigram+"卦"});});
  const a=[...m.values()].sort((x,y)=>x.value-y.value);setOpts($("trigramSelect"),a);$("trigramSelect").value="1";
}
function populateMountains(){
  const id=Number($("trigramSelect").value);
  const a=S.mountains.filter(x=>x.trigram_id===id);
  setOpts($("mountainSelect"),a,"id","label");
  updateMountain();
}
function updateMountain(){
  const m=currentMountain();if(!m)return;
  setOpts($("jianSelect"),m.jian);
  setOpts($("fenjinSelect"),m.fenjin.map(x=>({value:x,label:"【"+x+"】分金"})));
  $("mountainSummary").textContent=m.name+"山 · "+m.element+" · "+m.direction;
  const ms=Object.entries(S.options.month_favorable).filter(x=>x[1].includes(m.element)).map(x=>x[0]);
  $("favorableSummary").textContent=ms.join("、")+"月对"+m.element+"山有利";
}
function updateUseLabels(){
  const v=$("useType").value;
  const a=document.querySelector('label[for="mountainSelect"]');
  const b=document.querySelector('label[for="jianSelect"]');
  if(["安门","造门楼","旧坟立碑"].includes(v)){a.textContent=v==="旧坟立碑"?"碑向":"向位";b.textContent="兼向";}
  else{a.textContent="坐山";b.textContent="兼山";}
}
function selected(cls){return [...document.querySelectorAll(cls+":checked")].map(x=>x.value);}
function payload(){
  const d=parseDate($("anchorDate").value),r=Number($("rangeSelect").value);
  return{
    start_date:ymd(r<0?addDays(d,r):d),end_date:ymd(r<0?d:addDays(d,r)),
    use_type:$("useType").value,mountain_id:Number($("mountainSelect").value),
    jian:$("jianSelect").value,fenjin:$("fenjinSelect").value,life_years:$("lifeYears").value,
    favorable_months:selected(".month-check"),level:$("levelSelect").value,
    hours:selected(".hour-check").map(Number)
  };
}
function gradeClass(n){return n>=1&&n<=4?"grade-"+n:"";}
function hoursHtml(a){return a.map(x=>'<span class="hour-chip '+(x.recommended?"good":"")+'">'+esc(x.zhi)+'时 '+esc(x.ganzhi)+' · '+esc(x.relation)+'</span>').join("");}
function reasonsHtml(x){
  if(!$("showReasons").checked)return "";
  let h='<div class="reason-wrap">';
  if(x.good.length)h+='<div class="reason-good">吉：'+x.good.map(esc).join("；")+'</div>';
  if(x.bad.length)h+='<div class="reason-bad">忌：'+x.bad.map(esc).join("；")+'</div>';
  if(x.yi.length)h+='<div>通胜宜：'+x.yi.slice(0,10).map(esc).join("、")+'</div>';
  if(x.ji.length)h+='<div>通胜忌：'+x.ji.slice(0,10).map(esc).join("、")+'</div>';
  return h+"</div>";
}
function render(data){
  $("resultTitle").textContent=data.use_type+" · "+data.mountain.direction+"【"+data.mountain.name+"山】"+data.mountain.element;
  $("resultCount").textContent="共 "+data.count+" 个日课";
  $("statusText").textContent=data.life_ganzhi.length?"年命："+data.life_ganzhi.join("、"):"正体五行日课";
  const sh=data.results.find(x=>x.bad.some(y=>y.includes("三煞")));
  $("shaSummary").textContent=sh?sh.bad.find(y=>y.includes("三煞")):"当前结果中未触发正四方年三煞提示";
  if(!data.results.length){$("resultList").innerHTML='<div class="empty-state"><div class="empty-title">当前条件没有匹配日课</div><div>可扩大日期范围、放宽等级，或取消手动利月限定。</div></div>';return;}
  $("resultList").innerHTML=data.results.map(x=>{
    const firstGood=x.good.length?'<div class="reason-good">'+esc(x.good[0])+'</div>':"";
    const firstBad=x.bad.length?'<div class="reason-bad">'+esc(x.bad[0])+'</div>':"";
    return '<article class="day-card"><div class="day-main">'+
      '<div class="day-cell"><div class="day-date">'+esc(x.date)+'</div><div class="day-score">'+esc(x.lunar)+'</div></div>'+
      '<div class="day-cell"><div>年：'+esc(x.year_ganzhi)+'</div><div>月：'+esc(x.month_ganzhi)+'</div></div>'+
      '<div class="day-cell"><div class="day-ganzhi">'+esc(x.day_ganzhi)+'日</div><div class="day-score">'+esc(x.day_element)+' · '+esc(x.relation)+'</div></div>'+
      '<div class="day-cell"><span class="tag '+gradeClass(x.level)+'">'+esc(x.level_name)+'</span><div class="day-score">评分 '+x.score+'</div></div>'+
      '<div class="day-cell">'+firstGood+firstBad+'</div></div>'+
      reasonsHtml(x)+'<div class="hours">'+hoursHtml(x.hours)+'</div></article>';
  }).join("");
}
async function calculate(){
  $("resultList").innerHTML='<div class="loading">正在计算日课……</div>';$("resultCount").textContent="计算中";
  try{
    const r=await fetch("/api/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload())});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"计算失败");render(d);
  }catch(e){$("resultCount").textContent="计算失败";$("resultList").innerHTML='<div class="error-box">'+esc(e.message)+'</div>';}
}
async function init(){
  $("anchorDate").value=ymd(new Date());
  const r=await fetch("/api/options");S.options=await r.json();S.mountains=S.options.mountains;
  setOpts($("useType"),S.options.use_types);setOpts($("levelSelect"),S.options.levels);$("levelSelect").value="小吉";
  populateHours();populateMonths();populateTrigrams();populateMountains();updateUseLabels();
  $("trigramSelect").onchange=populateMountains;$("mountainSelect").onchange=updateMountain;$("useType").onchange=updateUseLabels;
  $("shanjiaForm").onsubmit=e=>{e.preventDefault();calculate();};$("calculateTop").onclick=calculate;
  $("restoreView").onclick=()=>{document.querySelector(".input-panel").scrollTop=0;document.querySelector(".result-panel").scrollTop=0;};
  calculate();
}
init().catch(e=>$("resultList").innerHTML='<div class="error-box">初始化失败：'+esc(e.message)+'</div>');
