
const S={options:null,mountains:[],repair:new Set(),repairPalace:""};
const $=id=>document.getElementById(id);
const GAN="甲乙丙丁戊己庚辛壬癸";
const ZHI="子丑寅卯辰巳午未申酉戌亥";
const MONTH_ZHI=["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"];

function ymd(d){return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function ymdParts(y,m,d){return y+"-"+String(m).padStart(2,"0")+"-"+String(d).padStart(2,"0");}
function ganzhiYear(y){const i=((y-4)%60+60)%60;return GAN[i%10]+ZHI[i%12];}
function ganzhiMonths(y){
  const yStem=((y-4)%10+10)%10;
  const firstStem=(yStem*2+2)%10;
  return MONTH_ZHI.map((zhi,i)=>GAN[(firstStem+i)%10]+zhi);
}
function populateGanzhiToolbar(){
  const now=new Date(), currentYear=now.getFullYear();
  const years=[];
  for(let y=1990;y<=2048;y++)years.push({value:String(y),label:y+ganzhiYear(y)+"年"});
  setOpts($("ganzhiYearSelect"),years);
  $("ganzhiYearSelect").value=String(Math.min(2048,Math.max(1990,currentYear)));
  refreshGanzhiMonths();
  const idx=(now.getMonth()+11)%12;
  $("ganzhiMonthSelect").selectedIndex=idx;
  setOpts($("ganzhiDaySelect"),["全部",...GAN.split(""),...ZHI.split("")].map(x=>({value:x,label:x==="全部"?"全部":x+"日"})));
  syncGanzhiTitles();
}
function refreshGanzhiMonths(){
  const y=Number($("ganzhiYearSelect").value)||new Date().getFullYear();
  const old=$("ganzhiMonthSelect").value;
  setOpts($("ganzhiMonthSelect"),ganzhiMonths(y).map(x=>({value:x,label:x+"月"})));
  if(old && [...$("ganzhiMonthSelect").options].some(o=>o.value===old))$("ganzhiMonthSelect").value=old;
  syncGanzhiTitles();
}
function syncGanzhiTitles(){
  const year=$("ganzhiYearSelect")?.value;
  const month=$("ganzhiMonthSelect")?.value;
  if(year && month){
    if($("monthShaTitle"))$("monthShaTitle").textContent=month+"月凶煞表";
    if($("yearShaTitle"))$("yearShaTitle").textContent=ganzhiYear(Number(year))+"年凶煞【点击选择】不利";
    if($("nextYearShaTitle"))$("nextYearShaTitle").textContent=ganzhiYear(Number(year)+1)+"年凶煞【点击选择】";
  }
}
function parseDate(s){const a=s.split("-").map(Number);return new Date(a[0],a[1]-1,a[2]);}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x;}
function esc(v){return String(v==null?"":v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
function setOpts(el,items,vk,lk){
  vk=vk||"value";lk=lk||"label";el.innerHTML="";
  items.forEach(x=>{const o=document.createElement("option");if(typeof x==="string"){o.value=x;o.textContent=x;}else{o.value=x[vk];o.textContent=x[lk];}el.appendChild(o);});
}
function currentMountain(){const id=Number($("mountainSelect").value);return S.mountains.find(x=>x.id===id)||S.mountains[0];}
function currentMeta(){return S.options.use_meta[$("useType").value]||{};}
function selected(cls){return [...document.querySelectorAll(cls+":checked")].map(x=>x.value);}

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
  const a=S.options.trigrams.filter(x=>x.value!==5);
  setOpts($("trigramSelect"),a);
  $("trigramSelect").value="1";
}
function populateMountains(preserveId){
  const id=Number($("trigramSelect").value);
  const meta=currentMeta();
  const a=S.mountains.filter(x=>x.trigram_id===id).map(x=>({
    id:x.id,
    label:meta.mountain_mode==="facing"?x.facing_label:x.label
  }));
  setOpts($("mountainSelect"),a,"id","label");
  if(preserveId && a.some(x=>x.id===preserveId))$("mountainSelect").value=String(preserveId);
  updateMountain();
}
function updateMountain(){
  const m=currentMountain();if(!m)return;
  setOpts($("jianSelect"),m.jian);
  setOpts($("fenjinSelect"),m.fenjin.map(x=>({value:x,label:"【"+x+"】分金"})));
  setOpts($("daguaSelect"),m.dagua);
  const meta=currentMeta();
  $("mountainSummary").textContent=m.name+(meta.mountain_mode==="facing"?"向":"山")+" · "+m.element+" · "+(meta.mountain_mode==="facing"?m.facing_direction:m.direction);
  $("favorableSummary").textContent=m.auto_favorable_months.join("、")+"月";
  applyAutoRepair();
}
function setHidden(id,hidden){$(id).hidden=!!hidden;}
function stepTitle(id,n,text){$(id).textContent="第"+n+"步【"+text+"】";}

function updateUseMeta(){
  const meta=currentMeta();
  const keep=currentMountain()?.id;
  setHidden("mountainStep",!meta.show_mountain);
  setHidden("repairStep",!meta.show_repair);
  setHidden("deceasedStep",!meta.show_deceased);
  setHidden("yearShaStep",!meta.show_year_sha);
  setHidden("relationGrid",meta.month_mode!=="relation");

  $("trigramLabel").textContent=meta.mountain_mode==="facing"?"向卦":"坐卦";
  $("mountainLabel").textContent=meta.mountain_mode==="facing"?"向位":"坐山";
  $("jianLabel").textContent=meta.mountain_mode==="facing"?"兼向":"兼山";

  let n=2;
  if(meta.show_mountain){$("mountainStepTitle").textContent=meta.mountain_title;n++;}
  if(meta.show_repair){stepTitle("repairStepTitle",n++,"选择修方");}
  stepTitle("lifeStepTitle",n++,"添加"+meta.life_name);
  if(meta.show_deceased){stepTitle("deceasedStepTitle",n++,"添加仙命");}
  if(meta.show_year_sha){stepTitle("yearShaStepTitle",n++,"查年煞");}
  stepTitle("monthStepTitle",n++,"添加利月");
  stepTitle("filterStepTitle",n++,"日课筛选功能");

  if(meta.month_mode==="relation"){
    const wanted=new Set(meta.default_month_relations||["旺","生","耗"]);
    document.querySelectorAll(".relation-check").forEach(x=>x.checked=wanted.has(x.value));
  }
  populateMountains(keep);
}
function renderRepair(){
  const values=[...S.repair];
  $("selectedRepair").textContent=values.length?values.join("；"):"未选择修方";
}
function setRepairPalace(palace){
  S.repairPalace=palace;
  const positions=S.options.repair_positions[palace]||[];
  $("repairPositionGrid").innerHTML=positions.map(x=>'<button type="button" class="repair-button repair-pos" data-value="'+esc(x)+'">'+esc(x)+'</button>').join("");
}
function addRepair(v){if(v){S.repair.add(v);renderRepair();}}
function clearRepair(){S.repair.clear();S.repairPalace="";$("repairPositionGrid").innerHTML="";renderRepair();}
function setupRepair(){
  $("repairDirectionGrid").innerHTML=S.options.repair_directions.map(x=>
    '<button type="button" class="repair-button repair-dir" data-value="'+esc(x.value)+'">'+esc(x.label)+'</button>'
  ).join("");
  $("repairDirectionGrid").onclick=e=>{
    const b=e.target.closest(".repair-dir");if(!b)return;
    addRepair(b.dataset.value);setRepairPalace(b.dataset.value);
  };
  $("repairPositionGrid").onclick=e=>{
    const b=e.target.closest(".repair-pos");if(!b)return;addRepair(b.dataset.value);
  };
  $("clearRepair").onclick=clearRepair;
}
function oppositeMountain(m){
  if(!m)return null;
  const idx=S.mountains.findIndex(x=>x.id===m.id);
  return idx<0?null:S.mountains[(idx+12)%24];
}
function applyAutoRepair(){
  const meta=currentMeta(),m=currentMountain();
  if(!meta.show_repair||!meta.auto_repair||!m)return;
  clearRepair();
  addRepair(m.trigram+"宫");addRepair(m.name);
  if(meta.auto_repair==="seat_facing"){
    const o=oppositeMountain(m);
    if(o){addRepair(o.trigram+"宫");addRepair(o.name);}
  }
}
function autoMonths(){
  const meta=currentMeta();
  if(meta.month_mode==="relation"){
    const wanted=new Set(meta.default_month_relations||["旺","生","耗"]);
    document.querySelectorAll(".relation-check").forEach(x=>x.checked=wanted.has(x.value));
    return;
  }
  const wanted=new Set(currentMountain()?.auto_favorable_months||[]);
  document.querySelectorAll(".month-check").forEach(x=>x.checked=wanted.has(x.value));
}
function payload(){
  const y=Number($("ganzhiYearSelect").value),m=currentMountain();
  const dagua=$("daguaSelect");
  return{
    start_date:ymdParts(y,1,15),end_date:ymdParts(y+1,2,15),
    ganzhi_year:ganzhiYear(y),ganzhi_month:$("ganzhiMonthSelect").value,
    ganzhi_day_filter:$("ganzhiDaySelect").value,
    use_type:$("useType").value,use_type_code:currentMeta().code,yiji_mode:$("editionSelect").value,mountain_id:Number($("mountainSelect").value),
    jian:$("jianSelect").value,fenjin:$("fenjinSelect").value,
    dagua:dagua.options[dagua.selectedIndex]?.text||"",dagua_value:dagua.value,
    repair_positions:[...S.repair],life_years:$("lifeYears").value,deceased_years:$("deceasedYears").value,
    favorable_months:selected(".month-check"),month_relations:selected(".relation-check"),level:$("levelSelect").value,
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
  const meta=currentMeta();
  $("resultTitle").textContent=data.use_type+" · "+(meta.mountain_mode==="facing"?data.mountain.facing_direction:data.mountain.direction)+"【"+data.mountain.name+(meta.mountain_mode==="facing"?"向":"山")+"】"+data.mountain.element;
  $("resultCount").textContent="共 "+data.count+" 个日课";
  let status=data.life_ganzhi.length?"年命："+data.life_ganzhi.join("、"):"正体五行日课";
  if(data.deceased_ganzhi?.length)status+="　仙命："+data.deceased_ganzhi.join("、");
  $("statusText").textContent=status;
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
  const r=await fetch("/api/options");S.options=await r.json();S.mountains=S.options.mountains;
  setOpts($("useType"),S.options.use_types);setOpts($("levelSelect"),S.options.levels);$("levelSelect").value="大吉";
  populateGanzhiToolbar();populateHours();populateMonths();populateTrigrams();setupRepair();
  $("ganzhiYearSelect").onchange=()=>{refreshGanzhiMonths();calculate();};
  $("ganzhiMonthSelect").onchange=()=>{syncGanzhiTitles();calculate();};
  $("ganzhiDaySelect").onchange=calculate;$("editionSelect").onchange=calculate;
  $("trigramSelect").onchange=()=>populateMountains();
  $("mountainSelect").onchange=updateMountain;
  $("useType").onchange=updateUseMeta;
  $("autoMonths").onclick=autoMonths;
  $("yearShaButton").onclick=calculate;
  $("shanjiaForm").onsubmit=e=>{e.preventDefault();calculate();};
  $("calculateTop").onclick=calculate;
  $("restoreView").onclick=()=>{document.querySelector(".input-panel").scrollTop=0;document.querySelector(".result-panel").scrollTop=0;};
  updateUseMeta();
  calculate();
}
init().catch(e=>$("resultList").innerHTML='<div class="error-box">初始化失败：'+esc(e.message)+'</div>');
