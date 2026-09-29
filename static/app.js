
const S={options:null,mountains:[],repair:new Set(),repairPalace:"",lifeEntries:[],deceasedEntries:[],favorableMonths:[],yearRequest:0,monthRequest:0,calculateRequest:0,searchMode:"evaluation",lastData:null,favorites:new Set(),selectedLessons:new Set(),initialPanelsPositioned:false};
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
function setCalendarType(){
  const mode=$("calendarType").value;
  const now=new Date(),year=Number($("ganzhiYearSelect").value)||now.getFullYear();
  if(mode==="干支"){
    setOpts($("ganzhiYearSelect"),Array.from({length:59},(_,i)=>{const y=1990+i;return {value:String(y),label:y+ganzhiYear(y)+"年"};}));
    $("ganzhiYearSelect").value=String(year);
    refreshGanzhiMonths();
    $("ganzhiMonthSelect").selectedIndex=(now.getMonth()+11)%12;
    setOpts($("ganzhiDaySelect"),["全部",...GAN.split(""),...ZHI.split("")].map(x=>({value:x,label:x==="全部"?"全部":x+"日"})));
  }else{
    setOpts($("ganzhiYearSelect"),Array.from({length:59},(_,i)=>({value:String(1990+i),label:(1990+i)+"年"})));
    $("ganzhiYearSelect").value=String(year);
    const lunarNames=["正","二","三","四","五","六","七","八","九","十","十一","十二"];
    setOpts($("ganzhiMonthSelect"),Array.from({length:12},(_,i)=>({value:String(i+1),label:mode==="农历"?lunarNames[i]+"月":(i+1)+"月"})));
    $("ganzhiMonthSelect").value=String(now.getMonth()+1);
    setOpts($("ganzhiDaySelect"),[{value:"全部",label:"全部"},...Array.from({length:31},(_,i)=>({value:String(i+1),label:(i+1)+"日"}))]);
  }
  $("ganzhiDaySelect").value="全部";
  loadMonthSha();
  loadYearSha();
  calculate("evaluation");
}
function syncGanzhiTitles(){
  const year=$("ganzhiYearSelect")?.value;
  const month=$("ganzhiMonthSelect")?.value;
  if(year && month){
    if($("monthShaTitle")&&$("calendarType").value==="干支")$("monthShaTitle").textContent=month+"月凶煞表";
  }
}
async function loadMonthSha(){
  const year=Number($("ganzhiYearSelect").value),month=$("ganzhiMonthSelect").value;
  if(!year||!month)return;
  if($("calendarType").value!=="干支"){$("monthShaTitle").textContent="月凶煞表";$("monthShaRows").textContent="请选择干支月份查看已核对的月表。";return;}
  const requestId=++S.monthRequest;
  try{
    const response=await fetch('/api/month-sha?year='+year+'&month='+encodeURIComponent(month));
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'无法读取月煞');
    if(requestId!==S.monthRequest)return;
    $("monthShaTitle").textContent=month+'月凶煞表';
    if(data.reference_verified){
      const parts=data.visible_text.split(/\n\n(?=[^\n]+月吉神表)/);
      const bad=parts[0].split('\n').slice(1);
      const good=(parts[1]||'').split('\n');
      const row=line=>{const match=line.match(/^【([^】]+)】\s*(.*)$/);return match?'<div class="sha-line"><span>【'+esc(match[1])+'】</span>'+esc(match[2])+'</div>':'';};
      $("monthShaRows").innerHTML=bad.map(row).join('')+'<div class="left-section-header">'+esc(good.shift()||month+'月吉神表')+'</div>'+good.map(row).join('');
    }else $("monthShaRows").textContent='这月的凶煞表尚未与原站核对。';
    if(!S.initialPanelsPositioned){
      S.initialPanelsPositioned=true;
      requestAnimationFrame(()=>{
        document.querySelector('.left-panel').scrollTop=Math.max(0,$("leftExtras").offsetTop-190);
        document.querySelector('.input-panel').scrollTop=Math.max(0,$("filterStep").offsetTop+235);
      });
    }
  }catch(error){if(requestId===S.monthRequest)$("monthShaRows").textContent=error.message;}
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
    const rows=card.rows.map(row=>'<div class="year-sha-row'+(row.applies?' year-sha-hit':'')+'">【'+esc(row.name)+'】'+esc(row.value)+'</div>').join("");
    const expandedRows=items=>items.map(row=>'<div class="year-sha-row"><span>【'+esc(row.name)+'】</span><span>'+esc(row.value)+'</span></div>').join('');
    const extraSha=card.extra_sha?.length?expandedRows(card.extra_sha):'这年的补充凶煞尚未与原站核对。';
    const goodRows=card.good_rows?.length?expandedRows(card.good_rows):'这年的吉神明细尚未与原站核对。';
    const note=card.reference_rows_verified?'':'<div class="year-sha-note">其余年煞规则尚未核实；此处只显示已实现的项目。</div>';
    const selectable=[...$("ganzhiYearSelect").options].some(option=>option.value===String(card.year));
    return '<section class="year-box"><button type="button" class="choose-year year-title" data-year="'+card.year+'" '+(selectable?'':'disabled')+'>'+esc(card.ganzhi)+'年凶煞【点击选择】'+esc(card.status)+'</button>'+
      '<div class="year-list">'+rows+'<button type="button" class="year-expand" data-expand="sha" data-ganzhi="'+esc(card.ganzhi)+'" aria-expanded="false">【点击展开凶煞】</button><div class="year-extra" hidden>'+extraSha+'</div><button type="button" class="year-expand" data-expand="good" data-ganzhi="'+esc(card.ganzhi)+'" aria-expanded="false">'+esc(card.ganzhi)+'年吉神【点击展开】</button><div class="year-extra" hidden>'+goodRows+'</div>'+note+'</div></section>';
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
    l.innerHTML='<input class="hour-check" type="checkbox" value="'+x.hour+'">'+esc(x.label);
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
  // 下拉选项文字来自原站；星旺月的点击结果尚未逐项采集。
  // 这里按子星为命主所生、夫星为克命主的五行及各五行当令月份推算。
  const starMonths={
    "child:甲乙":["巳","午"],"child:丙丁":["辰","未","戌","丑"],
    "child:戊己":["申","酉"],"child:庚辛":["亥","子"],"child:壬癸":["寅","卯"],
    "spouse:甲乙":["申","酉"],"spouse:丙丁":["亥","子"],
    "spouse:戊己":["寅","卯"],"spouse:庚辛":["巳","午"],
    "spouse:壬癸":["辰","未","戌","丑"]
  };
  const lifeGroups=["甲乙","丙丁","戊己","庚辛","壬癸"];
  const options=[{value:"",label:"手动添加利月"},
    ...months.map(x=>({value:x,label:x+"月"+monthHints[x]+"山有利"})),
    {value:"all",label:"十二个月"},{value:"stove-heading",label:"以下是作灶馈主"},
    ...lifeGroups.map(x=>({value:"child:"+x,label:x+"命子星旺月"})),
    ...lifeGroups.map(x=>({value:"spouse:"+x,label:x+"命夫星旺月"}))];
  setOpts($("manualMonth"),options);
  for(const option of $("manualMonth").options){
    option.dataset.kind=option.value==="stove-heading"?"heading":option.value.startsWith("child:")?"child":option.value.startsWith("spouse:")?"spouse":"month";
    if(option.value==="stove-heading")option.disabled=true;
  }
  $("manualMonth").onchange=e=>{
    if(e.target.value==="all")S.favorableMonths=[...months];
    else if(months.includes(e.target.value)&&!S.favorableMonths.includes(e.target.value))S.favorableMonths.push(e.target.value);
    else if(starMonths[e.target.value]){
      for(const month of starMonths[e.target.value])if(!S.favorableMonths.includes(month))S.favorableMonths.push(month);
    }
    e.target.value="";
    renderMonths();
  };
  $("monthGrid").onclick=e=>{
    const remove=e.target.closest(".month-remove");
    if(!remove)return;
    S.favorableMonths=S.favorableMonths.filter(month=>month!==remove.dataset.month);
    renderMonths();
  };
  renderMonths();
}
function renderMonths(){
  $("monthGrid").innerHTML=S.favorableMonths.map(month=>
    '<div class="month-card"><input class="month-name" type="text" value="'+esc(month)+'" readonly tabindex="-1" aria-label="已选'+esc(month)+'月">'+
    '<button type="button" class="month-remove" data-month="'+esc(month)+'" aria-label="移除'+esc(month)+'月">X</button></div>'
  ).join("");
  $("monthGrid").hidden=currentMeta().month_mode==="relation"||!S.favorableMonths.length;
  $("selectedMonths").textContent=S.favorableMonths.length?"已选利月："+S.favorableMonths.join("、")+"月":"未限定利月";
}
function populateShaFilters(){
  const defaults=new Set(currentMeta().default_sha_filters||[]);
  const supported=new Set(S.options.supported_sha_filters);
  const groups=[
    ["月冲山","日冲山","时冲山"],["月三杀","日三杀","时三杀"],
    ["月正阴府","日正阴府","时正阴府"],["日正八煞","时正八煞"],
    ["五黄重叠","二五交加"],["月五黄煞","日五黄煞","时五黄煞"],
    ["日星曜煞","时星曜煞"],["天星煞","地曜煞"],
    ["日流太岁","日消灭煞"],["日山方煞","时山方煞"],
    ["月克山运","日克山运","时克山运"],["月傍阴府","日傍阴府","时傍阴府"]
  ];
  $("shaFilterGrid").innerHTML=groups.map(group=>'<div class="sha-filter-group">'+group.map(name=>{
    const usable=supported.has(name);
    const reason=name==='日流太岁'?'文档规则与原站已存结果尚未一致，暂不参与筛选':'当前本地算法尚未支持此项';
    return '<label class="'+(usable?'':'filter-unavailable')+'" title="'+(usable?'搜索时参与本地计算':reason)+'"><input '+(usable?'class="sha-filter-check"':'')+' type="checkbox" value="'+esc(name)+'" '+(usable&&defaults.has(name)?'checked':'')+' '+(usable?'':'disabled')+'>'+esc(name)+'</label>';
  }).join('')+'</div>').join("");
  const supportedJian=new Set(S.options.supported_jian_filters||[]);
  $("jianFilterGrid").innerHTML=['月冲兼山','日冲兼山','时冲兼山','兼山月三杀','兼山日三杀','兼山时三杀'].map(name=>{
    const usable=supportedJian.has(name);
    return '<label class="'+(usable?'':'filter-unavailable')+'" title="'+(usable?'搜索时按当前兼山参与计算':'当前本地算法尚未支持此项')+'"><input '+(usable?'class="jian-filter-check"':'')+' type="checkbox" value="'+esc(name)+'" '+(usable?'':'disabled')+'>'+name+'</label>';
  }).join('');
  syncAllShaFilters();
}
function populateFilterPositions(){
  const items=[{value:'',label:'X'},...S.mountains.map(m=>({value:m.name,label:'【'+m.name+'】位'})),{value:'中宫',label:'【中宫】位'}];
  const oldOne=currentMountain()?.name||'',oldTwo=$("filterPositionTwo").value;
  setOpts($("filterPositionOne"),items);setOpts($("filterPositionTwo"),items);
  $("filterPositionOne").value=oldOne||currentMountain()?.name||'';
  $("filterPositionTwo").value=oldTwo||'';
}
function syncAllShaFilters(){
  const filters=[...document.querySelectorAll(".sha-filter-check")];
  $("allShaFilters").checked=filters.length>0&&filters.every(x=>x.checked);
  $("allShaFilters").indeterminate=filters.some(x=>x.checked)&&!$("allShaFilters").checked;
}
function syncJianFilterAvailability(){
  const usable=$("jianSelect").value!=="正针";
  document.querySelectorAll('.jian-filter-check').forEach(input=>{
    input.disabled=!usable;
    if(!usable)input.checked=false;
    input.closest('label').classList.toggle('filter-unavailable',!usable);
    input.closest('label').title=usable?'搜索时按当前兼山参与计算':'正针没有兼山';
  });
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
  syncJianFilterAvailability();
  setOpts($("fenjinSelect"),m.fenjin.map(x=>({value:x,label:"【"+x+"】分金"})));
  setOpts($("daguaSelect"),m.dagua);
  const meta=currentMeta();
  $("mountainSummary").textContent=m.name+(meta.mountain_mode==="facing"?"向":"山")+" · "+m.element+" · "+(meta.mountain_mode==="facing"?m.facing_direction:m.direction);
  $("favorableSummary").textContent=m.auto_favorable_months.join("、")+"月";
  $("burialSummary").textContent=m.element==="水"?'水山：子、寅、申、辰、巽、甲、辛、丙：墓运':m.name+'山墓运资料尚未核对';
  $("societyDays").innerHTML=Number($("ganzhiYearSelect").value)===2026?'春社：二月初七<br>秋社：八月十一':'社日日期尚未核对';
  populateFilterPositions();
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
  renderMonths();
  $("monthStep").classList.toggle("month-mode",meta.month_mode!=="relation");

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
  S.favorableMonths=[...wanted];
  renderMonths();
}
function payload(mode=S.searchMode){
  const y=Number($("ganzhiYearSelect").value),m=currentMountain();
  const dagua=$("daguaSelect");
  const calendarMode=$("calendarType").value;
  const selectedMonth=Number($("ganzhiMonthSelect").value);
  const selectedDay=Number($("ganzhiDaySelect").value);
  let start=ymdParts(y,1,15),end=ymdParts(y+1,2,15);
  if(calendarMode==="公历"){
    start=ymdParts(y,selectedMonth||1,selectedDay||1);
    end=ymdParts(y,selectedMonth||12,selectedDay||new Date(y,selectedMonth||12,0).getDate());
  }
  return{
    start_date:start,end_date:end,evaluation_mode:mode==="evaluation",
    calendar_mode:calendarMode,calendar_year:calendarMode==="干支"?0:y,
    calendar_month:calendarMode==="干支"?0:selectedMonth,
    calendar_day:calendarMode==="干支"?0:selectedDay,
    ganzhi_year:calendarMode==="干支"?ganzhiYear(y):"",ganzhi_month:calendarMode==="干支"?$("ganzhiMonthSelect").value:"",
    ganzhi_day_filter:calendarMode==="干支"?$("ganzhiDaySelect").value:"",
    use_type:$("useType").value,use_type_code:currentMeta().code,yiji_mode:$("editionSelect").value,mountain_id:Number($("mountainSelect").value),
    jian:$("jianSelect").value,fenjin:$("fenjinSelect").value,
    dagua:dagua.options[dagua.selectedIndex]?.text||"",dagua_value:dagua.value,
    repair_positions:[...new Set([...S.repair,...[$("filterPositionOne").value,$("filterPositionTwo").value].filter(Boolean)])],life_years:yearEntries("life"),deceased_years:yearEntries("deceased"),
    life_sha_filter:$("lifeShaFilter").value==="on",sha_filters:selected(".sha-filter-check"),jian_filters:selected(".jian-filter-check"),
    favorable_months:currentMeta().month_mode==="relation"?[]:[...S.favorableMonths],month_relations:selected(".relation-check"),level:$("levelSelect").value,
    hours:selected(".hour-check").map(Number)
  };
}
function gradeClass(n){return n>=1&&n<=4?"grade-"+n:"";}
function dotList(a){return a?.length?a.map(esc).join(".")+".":"—";}
function dayHeader(x){
  const d=parseDate(x.date),week="日一二三四五六"[d.getDay()];
  const lunar=String(x.lunar||"").replace(/^[^年]*年/,"").replace(/日$/,"");
  return '<button type="button" class="card-print" data-print="'+esc(x.lesson_id)+'">[打印]</button>　农历:'+esc(d.getFullYear()+lunar+'日'+(x.lunar_month_size===30?'大':'小'))+'︴ 公历:'+esc((d.getMonth()+1)+'月'+d.getDate()+'日')+'︴ 星期'+week+'︴ 节气: '+esc(x.jieqi||'—')+'︴ 十二建星:'+esc(x.zhi_xing||'—')+'日 ︴ 二十八宿:'+esc(x.xiu||'—')+'宿'+esc(x.xiu_luck||'')+' ︴';
}
function methodPane(x,mountain){
  const checked=new Set(selected('.method-check'));
  const pillars=[x.year_ganzhi,x.month_ganzhi,x.day_ganzhi,x.time_ganzhi];
  const elements={甲:'木',乙:'木',丙:'火',丁:'火',戊:'土',己:'土',庚:'金',辛:'金',壬:'水',癸:'水'};
  const generates={木:'火',火:'土',土:'金',金:'水',水:'木'};
  const controls={木:'土',土:'水',水:'火',火:'金',金:'木'};
  const relation=(element)=>element===mountain.element?'旺':generates[element]===mountain.element?'泄':generates[mountain.element]===element?'生':controls[element]===mountain.element?'克':'耗';
  const pillarRow=(values,cls='')=>'<div class="pillar-line '+cls+'">'+values.map(v=>'<span>'+esc(v||'—')+'</span>').join('')+'</div>';
  const stemElements=pillars.map(p=>elements[p?.[0]]||'');
  const ds=x.doushou,dsRows=ds?.pillars||[];
  const dsLine=(field,cls='')=>'<div class="ds-row '+cls+'">'+dsRows.map(row=>'<span>'+esc(row[field]||'—')+'</span>').join('')+'</div>';
  const pillarsHtml=checked.has('斗首择日')?'<div class="wb-pillars" title="斗首五神、化气五行与十二长生"><div class="wb-red-head">斗首择日</div><div class="doushou-grid">'+
    dsLine('upper_star','ds-star')+dsLine('upper_element','ds-element')+
    '<div class="ds-row ds-stem">'+pillars.map(p=>'<span>'+esc(p?.[0]||'—')+'</span>').join('')+'</div>'+
    '<div class="ds-row ds-branch">'+pillars.map(p=>'<span>'+esc(p?.[1]||'—')+'</span>').join('')+'</div>'+
    dsLine('upper_stage','ds-stage')+dsLine('lower_star','ds-star')+
    dsLine('lower_element','ds-element')+dsLine('lower_stage','ds-stage')+
    '</div></div><div class="wb-doushou-mountain"><strong>山</strong><span>'+esc(mountain.name)+'山斗首属 <b>'+esc(ds?.mountain_element||'—')+'</b></span></div>':'<div class="wb-pillars method-muted">斗首择日已隐藏</div><div class="wb-doushou-mountain"></div>';
  const shanLabels=[...(x.shan_sha_labels?.length?x.shan_sha_labels:x.bad)];
  if(x.day_xiaomie&&!shanLabels.includes('日消灭煞'))shanLabels.push('日消灭煞');
  const hasShanYun=shanLabels.some(v=>/^山运[金木水火土]$/.test(v));
  const bad=shanLabels.length?shanLabels.map(v=>'<div'+(/^山运[金木水火土]$/.test(v)?' class="wb-accent"':'')+'>'+esc(v)+'</div>').join(''):'<div>本课未列山煞</div>';
  const star=x.flying_stars||{};
  const shanHtml='<div class="wb-sha"><div class="wb-gray-head">'+esc(mountain.name)+'山煞</div>'+(hasShanYun?'':'<div class="wb-accent">山运'+esc(x.shan_yun_element||mountain.element)+'</div>')+bad+'<div class="wb-accent">飞星</div><div>'+esc(star.facing||'—')+'向</div><div>'+esc(star.center||'—')+'中</div><div class="wb-star-seat">'+esc(star.seat||'—')+'坐</div></div>';
  const times=(x.jieqi_times||[]).map(t=>{const [day,time]=String(t.time||'').split(' ');return '<div class="jieqi-entry"><span>'+esc(t.name)+':'+esc(day||'')+'</span><span>'+esc(time||'')+'</span></div>';}).join('');
  const jieqiHtml='<div class="wb-jieqi"><div class="wb-red-head">节气时间</div>'+times+'</div>';
  const pieces=[pillarsHtml,shanHtml];
  // 原站的飞星和杀师煞属于日课基础列，单独显示斗首时仍在排盘右侧。
  pieces.push('<div class="wb-master-sha"><div class="wb-gray-head">杀师煞</div>'+(x.master_sha_labels||[]).map(v=>'<div>'+esc(v)+'</div>').join('')+'</div>');
  pieces.push(jieqiHtml);
  const unavailable=[...checked].filter(name=>!['斗首择日','玄空紫白'].includes(name));
  const signs=x.hour_signs?.length?x.hour_signs:[x.hours?.[0]?.recommended?'时吉':'时凶'];
  return '<div class="lesson-workbench">'+
    '<div class="wb-vertical"><strong>胎神</strong><span>'+esc(x.day_position_tai||'—')+'</span></div>'+
    '<div class="wb-vertical"><strong>门光星</strong><span>'+esc(x.men_guang||'—')+'</span></div>'+
    '<div class="wb-vertical wb-zhoutang"><strong>周堂</strong><span>'+esc(x.zhoutang||'—')+'</span></div>'+
    '<div class="wb-hour"><div class="wb-red-head">'+esc(x.hour)+'点</div>'+signs.slice(0,6).map((sign,i)=>'<div class="'+(i===0?'wb-red-head':'')+'">'+esc(sign)+'</div>').join('')+'</div>'+
    '<div class="wb-element"><div>'+esc(mountain.name)+'山属'+esc(mountain.element)+'</div><div>'+esc(x.reference_grade_label||x.level_name)+'</div>'+pillarRow(x.pillar_top_relations?.length===4?x.pillar_top_relations:stemElements.map(relation),'pillar-relation')+pillarRow(pillars.map(p=>p?.[0]),'pillar-stem')+pillarRow(pillars.map(p=>p?.[1]),'pillar-branch')+pillarRow(x.pillar_bottom_relations?.length===4?x.pillar_bottom_relations:stemElements.map((e,i)=>i===1?'令':relation(e)),'pillar-relation')+'<button type="button" class="twelve-hours" data-hours="'+esc(x.lesson_id)+'">查看十二时辰</button>'+pillarRow(x.pillar_nayin_elements||stemElements,'pillar-element')+'</div>'+
    '<div class="wb-choose"><label><input class="lesson-select" data-lesson="'+esc(x.lesson_id)+'" type="checkbox" '+(S.selectedLessons.has(x.lesson_id)?'checked':'')+'>选中</label><button type="button" class="favorite-button" data-favorite="'+esc(x.lesson_id)+'">'+(S.favorites.has(x.lesson_id)?'已收藏':'添加收藏')+'</button></div>'+
    pieces.join('')+'</div>'+
    (unavailable.length?'<div class="method-notice">'+unavailable.map(esc).join('、')+'：当前本地计算尚无排盘数据</div>':'')+
    '<div class="hours-detail" data-hours-detail="'+esc(x.lesson_id)+'" hidden></div>';
}
function renderCalendar(){
  if(!S.lastData)return;
  const first=S.lastData.results[0]?.date||ymd(new Date());
  const date=parseDate(first),year=date.getFullYear(),month=date.getMonth();
  $("calendarDialogTitle").textContent=year+'年'+(month+1)+'月日历';
  const lessons=new Map();
  S.lastData.results.forEach(x=>{const n=Number(x.date.slice(8));if(x.date.slice(0,7)===ymdParts(year,month+1,1).slice(0,7))lessons.set(n,(lessons.get(n)||0)+1);});
  const offset=new Date(year,month,1).getDay(),days=new Date(year,month+1,0).getDate();
  $("calendarGrid").innerHTML='日一二三四五六'.split('').map(x=>'<b>'+x+'</b>').join('')+Array.from({length:offset},()=>'<span></span>').join('')+Array.from({length:days},(_,i)=>'<button type="button" data-calendar-date="'+ymdParts(year,month+1,i+1)+'" class="'+(lessons.has(i+1)?'has-lesson':'')+'">'+(i+1)+(lessons.has(i+1)?'<small>'+lessons.get(i+1)+'课</small>':'')+'</button>').join('');
}
function render(data){
  S.lastData=data;
  const meta=currentMeta();
  $("resultTitle").textContent=data.use_type+" · "+(meta.mountain_mode==="facing"?data.mountain.facing_direction:data.mountain.direction)+"【"+data.mountain.name+(meta.mountain_mode==="facing"?"向":"山")+"】"+data.mountain.element;
  $("resultCount").textContent=data.count+"个日课。";
  let status=data.life_ganzhi.length?"年命："+data.life_ganzhi.join("、"):"正体五行日课";
  if(data.deceased_ganzhi?.length)status+="　仙命："+data.deceased_ganzhi.join("、");
  $("statusText").textContent=status;
  if(!data.results.length){$("resultList").innerHTML='<div class="empty-state">当前条件没有匹配日课。可改变日期、时辰或筛选项后重新搜索。</div>';return;}
  const order=$("sortSelect").value;
  const doushouOnly=selected('.method-check').length===1&&selected('.method-check')[0]==='斗首择日';
  const lessons=[...data.results];
  if(order==='山煞')lessons.sort((a,b)=>(a.shan_sha_labels?.length||a.bad.length)-(b.shan_sha_labels?.length||b.bad.length)||a.date.localeCompare(b.date)||a.hour-b.hour);
  else if(order!=='斗首择日')lessons.sort((a,b)=>b.score-a.score||a.date.localeCompare(b.date)||a.hour-b.hour);
  $("resultList").innerHTML=lessons.map(x=>'<article class="day-card'+(doushouOnly?' doushou-only':'')+'" data-card="'+esc(x.lesson_id)+'">'+
    '<div class="day-head">'+dayHeader(x)+'</div>'+
    '<div class="almanac-line line-yi"><b>宜事:</b> '+dotList(x.yi)+'</div>'+
    '<div class="almanac-line"><b>忌事:</b> '+dotList(x.ji)+'</div>'+
    '<div class="almanac-line line-good"><b>吉神:</b> '+dotList(x.ji_shen)+' '+esc(x.compass_gods_text||'')+'</div>'+
    '<div class="almanac-line"><b>凶煞:</b> '+dotList(x.xiong_sha)+'</div>'+
    (S.bookMode?'':methodPane(x,data.mountain))+'</article>').join('');
}
async function calculate(mode=S.searchMode){
  S.searchMode=mode;
  if($("lifeYears").value&&!$("lifeYears").reportValidity())return;
  if(currentMeta().show_deceased&&$("deceasedYears").value&&!$("deceasedYears").reportValidity())return;
  $("resultList").innerHTML='<div class="loading">正在计算日课……</div>';$("resultCount").textContent="计算中";
  const requestId=++S.calculateRequest;
  try{
    const r=await fetch("/api/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload(mode))});
    const d=await r.json();if(requestId!==S.calculateRequest)return;if(!r.ok)throw new Error(d.error||"计算失败");render(d);document.querySelector('.result-panel').scrollTop=0;
  }catch(e){if(requestId===S.calculateRequest){$("resultCount").textContent="计算失败";$("resultList").innerHTML='<div class="error-box">'+esc(e.message)+'</div>';}}
}
async function init(){
  const r=await fetch("/api/options");S.options=await r.json();S.mountains=S.options.mountains;
  try{S.favorites=new Set(JSON.parse(localStorage.getItem('selectdat-favorites')||'[]'));}catch(_){S.favorites=new Set();}
  setOpts($("useType"),S.options.use_types);setOpts($("levelSelect"),S.options.levels);$("levelSelect").value="全部";
  populateGanzhiToolbar();populateHours();populateMonths();populateTrigrams();setupRepair();setupYearEntries();
  $("calendarType").onchange=setCalendarType;
  $("ganzhiYearSelect").onchange=()=>{if($("calendarType").value==="干支")refreshGanzhiMonths();$("societyDays").innerHTML=Number($("ganzhiYearSelect").value)===2026?'春社：二月初七<br>秋社：八月十一':'社日日期尚未核对';loadYearSha();loadMonthSha();calculate('evaluation');};
  $("ganzhiMonthSelect").onchange=()=>{syncGanzhiTitles();loadMonthSha();calculate('evaluation');};
  $("ganzhiDaySelect").onchange=()=>calculate('evaluation');$("editionSelect").onchange=()=>calculate(S.searchMode);
  $("trigramSelect").onchange=()=>populateMountains();
  $("mountainSelect").onchange=updateMountain;
  $("useType").onchange=updateUseMeta;
  $("autoMonths").onclick=autoMonths;
  $("yearShaButton").onclick=()=>{
    document.querySelector(".year-panel").hidden=false;
    document.querySelector(".main-grid").classList.remove("year-hidden");
    const year=String(new Date().getFullYear());
    if([...$("ganzhiYearSelect").options].some(option=>option.value===year)){
      $("ganzhiYearSelect").value=year;
      if($("calendarType").value==="干支"){
        refreshGanzhiMonths();$("ganzhiMonthSelect").selectedIndex=(new Date().getMonth()+11)%12;syncGanzhiTitles();loadMonthSha();
      }
      loadYearSha();calculate('evaluation');
    }
    document.querySelector(".year-panel").scrollTop=0;
  };
  $("yearShaButtonInline").onclick=()=>{
    document.querySelector(".year-panel").hidden=false;
    document.querySelector(".main-grid").classList.remove("year-hidden");
    document.querySelector(".year-panel").scrollTop=0;
  };
  $("yearShaCards").onclick=e=>{
    const expand=e.target.closest('.year-expand');
    if(expand){const detail=expand.nextElementSibling;detail.hidden=!detail.hidden;expand.setAttribute('aria-expanded',String(!detail.hidden));expand.textContent=expand.dataset.expand==='sha'?(detail.hidden?'【点击展开凶煞】':'【点击收起凶煞】'):expand.dataset.ganzhi+'年吉神'+(detail.hidden?'【点击展开】':'【点击收起】');return;}
    const button=e.target.closest(".choose-year");if(!button)return;
    $("ganzhiYearSelect").value=button.dataset.year;
    if($("calendarType").value==="干支")refreshGanzhiMonths();loadYearSha();loadMonthSha();calculate('evaluation');
  };
  $("allShaFilters").onchange=e=>{document.querySelectorAll(".sha-filter-check").forEach(x=>x.checked=e.target.checked);syncAllShaFilters();calculate('selection');};
  $("shaFilterGrid").onchange=()=>{syncAllShaFilters();calculate('selection');};
  $("jianFilterGrid").onchange=()=>calculate('selection');
  $("jianSelect").onchange=()=>{syncJianFilterAvailability();calculate('selection');};
  $("resetShaFilters").onclick=()=>{populateShaFilters();calculate('selection');};
  $("filterPositionOne").onchange=()=>calculate('selection');$("filterPositionTwo").onchange=()=>calculate('selection');
  $("shanjiaForm").onsubmit=e=>{e.preventDefault();calculate('selection');};
  $("calculateTop").onclick=()=>calculate('evaluation');
  $("sortSelect").onchange=()=>{if(S.lastData)render(S.lastData);};
  document.querySelector('.method-row').onchange=()=>{if(S.lastData)render(S.lastData);};
  $("bookMode").onclick=()=>{S.bookMode=!S.bookMode;$("bookMode").classList.toggle('active',S.bookMode);$("bookMode").setAttribute('aria-pressed',String(!!S.bookMode));if(S.lastData)render(S.lastData);};
  $("resultList").onclick=async e=>{
    const print=e.target.closest('[data-print]');
    if(print){$("resultList").querySelectorAll('.print-target').forEach(x=>x.classList.remove('print-target'));print.closest('.day-card')?.classList.add('print-target');document.body.dataset.printLesson=print.dataset.print;window.print();return;}
    const favorite=e.target.closest('[data-favorite]');
    if(favorite){const id=favorite.dataset.favorite;S.favorites.has(id)?S.favorites.delete(id):S.favorites.add(id);localStorage.setItem('selectdat-favorites',JSON.stringify([...S.favorites]));favorite.textContent=S.favorites.has(id)?'已收藏':'添加收藏';return;}
    const hours=e.target.closest('[data-hours]');
    if(hours){
      const target=$("resultList").querySelector('[data-hours-detail="'+hours.dataset.hours+'"]');
      if(!target)return;
      if(!target.hidden){target.hidden=true;return;}
      target.hidden=false;target.textContent='正在计算十二时辰……';
      const lesson=S.lastData?.results.find(x=>x.lesson_id===hours.dataset.hours);if(!lesson)return;
      const p=payload('evaluation');p.start_date=lesson.date;p.end_date=lesson.date;p.hours=S.options.hours.map(x=>x.hour);
      try{const response=await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});const result=await response.json();if(!response.ok)throw new Error(result.error);target.innerHTML=result.results.map(x=>'<span>'+esc(x.time_zhi)+'时　'+esc(x.time_ganzhi)+'　'+esc(x.time_relation)+'</span>').join('');}
      catch(error){target.textContent=error.message||'读取失败';}
    }
  };
  $("resultList").onchange=e=>{if(e.target.classList.contains('lesson-select')){e.target.checked?S.selectedLessons.add(e.target.dataset.lesson):S.selectedLessons.delete(e.target.dataset.lesson);}};
  window.addEventListener('afterprint',()=>{delete document.body.dataset.printLesson;$("resultList").querySelectorAll('.print-target').forEach(x=>x.classList.remove('print-target'));});
  $("calendarViewSelect").onchange=e=>{if(e.target.value==='calendar'){renderCalendar();$("calendarDialog").showModal();}e.target.value='lessons';};
  $("closeCalendar").onclick=()=>$("calendarDialog").close();
  $("calendarGrid").onclick=e=>{const button=e.target.closest('[data-calendar-date]');if(!button)return;const lesson=S.lastData?.results.find(x=>x.date===button.dataset.calendarDate);const article=lesson?$("resultList").querySelector('[data-card="'+lesson.lesson_id+'"]'):null;$("calendarDialog").close();if(article)article.scrollIntoView({behavior:'smooth',block:'start'});};
  $("leftTop").onclick=()=>document.querySelector('.left-panel').scrollTo({top:0,behavior:'smooth'});
  document.querySelectorAll(".hide-panel").forEach(button=>button.onclick=()=>{
    const side=button.dataset.panel;
    document.querySelector("."+side+"-panel").hidden=true;
    document.querySelector(".main-grid").classList.add(side+"-hidden");
  });
  $("restoreView").onclick=()=>{
    for(const side of ["left","year","input"]){document.querySelector("."+side+"-panel").hidden=false;document.querySelector(".main-grid").classList.remove(side+"-hidden");}
    document.querySelector(".input-panel").scrollTop=0;document.querySelector(".result-panel").scrollTop=0;
  };
  updateUseMeta();
  loadMonthSha();
  calculate('evaluation');
}
init().catch(e=>$("resultList").innerHTML='<div class="error-box">初始化失败：'+esc(e.message)+'</div>');
