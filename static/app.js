
const S={options:null,mountains:[],repair:new Set(),repairPalace:"",lifeEntries:[],deceasedEntries:[],yearRequest:0};
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
  const oldIndex=$("ganzhiMonthSelect").selectedIndex;
  setOpts($("ganzhiMonthSelect"),ganzhiMonths(y).map(x=>({value:x,label:x+"月"})));
  if(old && [...$("ganzhiMonthSelect").options].some(o=>o.value===old))$("ganzhiMonthSelect").value=old;
  else if(oldIndex>=0)$("ganzhiMonthSelect").selectedIndex=oldIndex;
  syncGanzhiTitles();
}
function syncGanzhiTitles(){
  const year=$("ganzhiYearSelect")?.value;
  const month=$("ganzhiMonthSelect")?.value;
  if(year && month){
    if($("monthShaTitle"))$("monthShaTitle").textContent=month+"月凶煞表";
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

function renderYearSha(data){
  $("yearShaCards").innerHTML=data.cards.map((card,i)=>{
    const rows=card.rows.map(row=>'<div class="year-sha-row'+(row.applies?' year-sha-hit':'')+'"><span>【'+esc(row.name)+'】</span><span>'+esc(row.value)+'</span></div>').join("");
    const note=card.reference_rows_verified?'':'<div class="year-sha-note">其余年煞规则尚未核实；此处只显示已实现的项目。</div>';
    const selectable=[...$("ganzhiYearSelect").options].some(option=>option.value===String(card.year));
    return '<details class="year-box" '+(i<2?'open':'')+'><summary class="year-title">'+esc(card.ganzhi)+'年凶煞 <span>'+(card.san_sha_hits?'本山三煞不利':'点击查看')+'</span></summary>'+
      '<div class="year-list"><button type="button" class="choose-year" data-year="'+card.year+'" '+(selectable?'':'disabled')+'>选此年</button>'+rows+'<div class="year-san-sha'+(card.san_sha_hits?' danger':'')+'">【年三煞】'+esc(card.san_sha_direction)+'方'+(card.san_sha_hits?'（犯本山）':'')+'</div>'+note+'</div></details>';
  }).join("");
}
async function loadYearSha(){
  const year=Number($("ganzhiYearSelect").value), mountain=currentMountain();
  if(!year||!mountain)return;
  const requestId=++S.yearRequest;
  try{
    const response=await fetch('/api/year-sha?year='+year+'&mountain_id='+mountain.id);
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'无法读取年煞');
    if(requestId===S.yearRequest)renderYearSha(data);
  }catch(error){if(requestId===S.yearRequest)$("yearShaCards").innerHTML='<div class="error-box">'+esc(error.message)+'</div>';}
}

function setupYearEntries(){
  setOpts($("lifeStem"),GAN.split(""));
  function syncBranches(){
    const parity=GAN.indexOf($("lifeStem").value)%2;
    const old=$("lifeBranch").value;
    setOpts($("lifeBranch"),ZHI.split("").filter((_,i)=>i%2===parity));
    if([...$("lifeBranch").options].some(o=>o.value===old))$("lifeBranch").value=old;
  }
  $("lifeStem").onchange=syncBranches;syncBranches();
  function add(kind,value){
    const list=kind==="life"?S.lifeEntries:S.deceasedEntries;
    value=String(value||"").trim();
    if(!value)return;
    if(!list.includes(value))list.push(value);
    renderEntries(kind);
  }
  $("addLifeYear").onclick=()=>{const field=$("lifeYears");if(!field.reportValidity())return;add("life",field.value);field.value="";};
  $("addLifeGanzhi").onclick=()=>add("life",$("lifeStem").value+$("lifeBranch").value);
  $("addDeceasedYear").onclick=()=>{const field=$("deceasedYears");if(!field.reportValidity())return;add("deceased",field.value);field.value="";};
  for(const kind of ["life","deceased"]){
    $(kind+"Entries").onclick=e=>{
      const button=e.target.closest("button[data-index]");if(!button)return;
      (kind==="life"?S.lifeEntries:S.deceasedEntries).splice(Number(button.dataset.index),1);
      renderEntries(kind);
    };
  }
  $("lifeYears").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();$("addLifeYear").click();}};
  $("deceasedYears").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();$("addDeceasedYear").click();}};
}
function renderEntries(kind){
  const list=kind==="life"?S.lifeEntries:S.deceasedEntries;
  $(kind+"Entries").innerHTML=list.map((value,index)=>'<span class="entry-chip">'+esc(value)+'<button type="button" data-index="'+index+'" aria-label="删除'+esc(value)+'">×</button></span>').join("");
}
function yearEntries(kind){
  const list=kind==="life"?S.lifeEntries:S.deceasedEntries;
  const draft=$(kind==="life"?"lifeYears":"deceasedYears").value.trim();
  return [...new Set([...list,...(draft?[draft]:[])])];
}

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
  const months=["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"];
  const monthHints={寅:"木火",卯:"木火",辰:"土金",巳:"火土",午:"火土",未:"土",申:"金水",酉:"金水",戌:"土金",亥:"水木",子:"水木",丑:"土金"};
  $("monthGrid").innerHTML=months
    .map(x=>'<label><input class="month-check" type="checkbox" value="'+x+'">'+x+'月</label>').join("");
  setOpts($("manualMonth"),[{value:"",label:"手动添加利月"},...months.map(x=>({value:x,label:x+"月"+monthHints[x]+"山有利"}))]);
  $("manualMonth").onchange=e=>{
    if(e.target.value){$("monthGrid").querySelector('input[value="'+e.target.value+'"]').checked=true;updateMonthSummary();}
    e.target.value="";
  };
  $("monthGrid").onchange=updateMonthSummary;
  updateMonthSummary();
}
function updateMonthSummary(){
  const months=selected(".month-check");
  $("selectedMonths").textContent=months.length?"已选利月："+months.join("、")+"月":"未限定利月";
}
function populateShaFilters(){
  const defaults=new Set(currentMeta().default_sha_filters||[]);
  $("shaFilterGrid").innerHTML=S.options.supported_sha_filters.map(name=>'<label><input class="sha-filter-check" type="checkbox" value="'+esc(name)+'" '+(defaults.has(name)?'checked':'')+'>'+esc(name)+'</label>').join("");
  syncAllShaFilters();
}
function syncAllShaFilters(){
  const filters=[...document.querySelectorAll(".sha-filter-check")];
  $("allShaFilters").checked=filters.length>0&&filters.every(x=>x.checked);
  $("allShaFilters").indeterminate=filters.some(x=>x.checked)&&!$("allShaFilters").checked;
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
  loadYearSha();
}
function setHidden(id,hidden){$(id).hidden=!!hidden;}
function stepTitle(id,n,text){$(id).textContent="第"+["","一","二","三","四","五","六","七","八"][n]+"步【"+text+"】";}

function updateUseMeta(){
  const meta=currentMeta();
  const keep=currentMountain()?.id;
  setHidden("mountainStep",!meta.show_mountain);
  setHidden("repairStep",!meta.show_repair);
  setHidden("deceasedStep",!meta.show_deceased);
  setHidden("yearShaStep",!meta.show_year_sha);
  setHidden("relationGrid",meta.month_mode!=="relation");
  setHidden("manualMonth",meta.month_mode==="relation");
  setHidden("monthGrid",meta.month_mode==="relation");
  setHidden("selectedMonths",meta.month_mode==="relation");

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
  populateShaFilters();
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
  updateMonthSummary();
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
    repair_positions:[...S.repair],life_years:yearEntries("life"),deceased_years:yearEntries("deceased"),
    life_sha_filter:$("lifeShaFilter").value==="on",sha_filters:selected(".sha-filter-check"),
    favorable_months:currentMeta().month_mode==="relation"?[]:selected(".month-check"),month_relations:selected(".relation-check"),level:$("levelSelect").value,
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
  if($("lifeYears").value&&!$("lifeYears").reportValidity())return;
  if(currentMeta().show_deceased&&$("deceasedYears").value&&!$("deceasedYears").reportValidity())return;
  $("resultList").innerHTML='<div class="loading">正在计算日课……</div>';$("resultCount").textContent="计算中";
  try{
    const r=await fetch("/api/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload())});
    const d=await r.json();if(!r.ok)throw new Error(d.error||"计算失败");render(d);
  }catch(e){$("resultCount").textContent="计算失败";$("resultList").innerHTML='<div class="error-box">'+esc(e.message)+'</div>';}
}
async function init(){
  const r=await fetch("/api/options");S.options=await r.json();S.mountains=S.options.mountains;
  setOpts($("useType"),S.options.use_types);setOpts($("levelSelect"),S.options.levels);$("levelSelect").value="大吉";
  populateGanzhiToolbar();populateHours();populateMonths();populateTrigrams();setupRepair();setupYearEntries();
  $("ganzhiYearSelect").onchange=()=>{refreshGanzhiMonths();loadYearSha();calculate();};
  $("ganzhiMonthSelect").onchange=()=>{syncGanzhiTitles();calculate();};
  $("ganzhiDaySelect").onchange=calculate;$("editionSelect").onchange=calculate;
  $("trigramSelect").onchange=()=>populateMountains();
  $("mountainSelect").onchange=updateMountain;
  $("useType").onchange=updateUseMeta;
  $("autoMonths").onclick=autoMonths;
  $("yearShaButton").onclick=()=>{
    document.querySelector(".year-panel").hidden=false;
    document.querySelector(".main-grid").classList.remove("year-hidden");
    const year=String(new Date().getFullYear());
    if([...$("ganzhiYearSelect").options].some(option=>option.value===year)){
      $("ganzhiYearSelect").value=year;refreshGanzhiMonths();
      $("ganzhiMonthSelect").selectedIndex=(new Date().getMonth()+11)%12;
      syncGanzhiTitles();loadYearSha();calculate();
    }
    document.querySelector(".year-panel").scrollTop=0;
  };
  $("yearShaButtonInline").onclick=()=>{
    document.querySelector(".year-panel").hidden=false;
    document.querySelector(".main-grid").classList.remove("year-hidden");
    document.querySelector(".year-panel").scrollTop=0;
  };
  $("yearShaCards").onclick=e=>{
    const button=e.target.closest(".choose-year");if(!button)return;
    $("ganzhiYearSelect").value=button.dataset.year;
    refreshGanzhiMonths();loadYearSha();calculate();
  };
  $("allShaFilters").onchange=e=>{document.querySelectorAll(".sha-filter-check").forEach(x=>x.checked=e.target.checked);syncAllShaFilters();};
  $("shaFilterGrid").onchange=syncAllShaFilters;
  $("resetShaFilters").onclick=populateShaFilters;
  $("shanjiaForm").onsubmit=e=>{e.preventDefault();calculate();};
  $("calculateTop").onclick=calculate;
  document.querySelectorAll(".hide-panel").forEach(button=>button.onclick=()=>{
    const side=button.dataset.panel;
    document.querySelector("."+side+"-panel").hidden=true;
    document.querySelector(".main-grid").classList.add(side+"-hidden");
  });
  $("restoreView").onclick=()=>{
    for(const side of ["year","input"]){document.querySelector("."+side+"-panel").hidden=false;document.querySelector(".main-grid").classList.remove(side+"-hidden");}
    document.querySelector(".input-panel").scrollTop=0;document.querySelector(".result-panel").scrollTop=0;
  };
  updateUseMeta();
  calculate();
}
init().catch(e=>$("resultList").innerHTML='<div class="error-box">初始化失败：'+esc(e.message)+'</div>');
