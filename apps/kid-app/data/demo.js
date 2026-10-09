/* Demo data (?demo=1): built-in sample, same shape as the server's view. Never talks to the hub. */
const weekdayMon0 = d => (d.getDay()+6)%7;
const DEMO = (() => {
  const META={Maths:['Mat','core'],German:['Ger','core'],English:['Eng','core'],French:['Fre','core'],Biology:['Bio','minor'],Geography:['Geo','minor'],History:['His','minor'],Sport:['Spo','minor'],Ethics:['Eth','minor'],Music:['Mus','elective'],Art:['Art','elective']};
  const L=(wd,s,e,t,n)=>({weekday:wd,start:s,end:e,title:t,kind:'lesson',note:n,code:META[t][0],subject_kind:META[t][1]});
  const B=(wd,s,e,t,n,k='break')=>({weekday:wd,start:s,end:e,title:t,kind:k,note:n});
  const days = {
    0:[['Maths','4a'],['German','4a'],['Biology','R6'],['Geography','4a'],['Sport','Gym']],
    1:[['German','4a'],['German','4a'],['Maths','4a'],['Maths','4a'],['Art','R12'],['English','4a']],
    2:[['Music','C1'],['Music','C1'],['English','4a'],['History','4a'],['Biology','R6'],['Maths','4a']],
    3:[['French','4a'],['French','4a'],['History','4a'],['English','4a'],['Maths','4a']],
    4:[['Sport','Gym'],['Sport','Gym'],['Ethics','R3'],['Maths','4a'],['German','4a']],
  };
  const times=[['08:00','08:45'],['08:45','09:30'],['09:50','10:35'],['10:35','11:20'],['11:35','12:20'],['13:00','13:45']];
  const slots=[];
  Object.entries(days).forEach(([d,ls])=>{ ls.forEach((l,i)=>slots.push(L(+d,times[i][0],times[i][1],l[0],l[1])));
    slots.push(B(+d,'09:30','09:50','Recess','Schoolyard, bring a snack'),B(+d,'11:20','11:35','Short break',null),B(+d,'12:20','13:00','Lunch','Canteen','meal')); });
  const g=(type,grade,note)=>({type,grade,note:note||null});
  const subj=(name,kind,w,o)=>{ const a=x=>x.length?x.reduce((s,y)=>s+y,0)/x.length:null; const wa=a(w),oa=a(o); const p=kind==='core'?.5:kind==='minor'?.3:.2;
    return {name,kind,average:+((wa!=null&&oa!=null)?wa*p+oa*(1-p):(wa??oa)).toFixed(2),grades:[...w.map(x=>g('written',x)),...o.map(x=>g('oral',x))]}; };
  const subjects=[subj('German','core',[3,2],[2,2]),subj('Maths','core',[2,2],[2,1]),subj('English','core',[3],[3,2]),subj('Biology','minor',[2],[1,2]),
                  subj('Geography','minor',[3],[2]),subj('Music','elective',[],[1,1]),subj('Art','elective',[],[2]),subj('Sport','minor',[],[1])];
  const wk=i=>{ const d=new Date(); d.setDate(d.getDate()-6+i); return {day:d.toISOString().slice(0,10),due:true,status:i===3?null:'given'}; };
  return {
    demo:true, privacy:{grades:{min_age:10,age:10,eligible:true,chosen:false,private:false},health:{min_age:14,age:10,eligible:false,chosen:false,private:false}}, child:{name:'Mila'}, subjects:Object.entries(META).map(([name,[code,kind]])=>({name,code,kind})), share:{timetable:true,stars:true,reminders:true,homework:true,activities:true,bag:true,grades:true,health:true},
    school:{slots},
    reminders:{today:[{id:'r1',title:'Bring your recorder',day_part:'morning',state:null},{id:'r3',title:'Pack the swim bag',day_part:'evening',state:null}],tomorrow:[{id:'r2',title:'Hand in the trip form',day_part:null,state:null}]},
    stars:{total:23,week:[1,1,0,1,0,0,0],goals:[
      {id:'a',title:'Movie night, pick the film',note:'Family goal',cost:20,have:23,reached:true,approved:false},
      {id:'b',title:'Sleepover with friends',note:'A parent plans it with you',cost:50,have:23,reached:false,approved:false},
      {id:'c',title:'Hang out outside the home',note:'Agreed time and place',cost:100,have:23,reached:false,approved:false}],
      chores:[{id:'t',title:'Set the table',day_part:'evening',done:true,star:true,outcome:'well'},{id:'d',title:'Unload the dishwasher',day_part:'morning',done:false,star:true,outcome:null},
              {id:'r',title:'Tidy your room',day_part:'day',done:false,star:false,outcome:null}]},
    homework:{subjects:Object.entries(META).map(([name,[code,kind]])=>({name,code,kind})),tasks:(()=>{ const day=n=>{const d=new Date();d.setDate(d.getDate()+n);return d.toISOString().slice(0,10);};
      const t=(id,kind,subject,title,n,by,done)=>({id,kind,subject,title,due_on:day(n),note:null,done:!!done,done_on:done?day(0):null,by,days:n});
      return [t('h1','homework','Geography','Map of Europe: colour the rivers',-1,'child'),t('h2','homework','Maths','Worksheet 4: fractions',1,'child'),t('h3','homework','German','Read chapter 3 and write a summary',2,'parent'),
        t('h4','test','English','Vocabulary test, unit 5',6,'child'),t('h5','test','Biology','Cells and organs',11,'parent'),t('h6','homework','Art','Bring a drawing of your street',3,'parent',true)]; })()},
    activities:(()=>{ const day=n=>{const d=new Date();d.setDate(d.getDate()+n);return d.toISOString().slice(0,10);};
      return {weekly:[{name:'Swimming',icon:'🏊',place:'Stadtbad',start:'17:00',end:'18:00',weekdays:[2],mode:'cycle',travel_minutes:10,leave_by:'16:50',escort:'independent',escort_name:null},
                      {name:'Football training',icon:'⚽',place:'Sportpark',start:'10:00',end:'11:30',weekdays:[5],mode:'car',travel_minutes:20,leave_by:'09:40',escort:'parent',escort_name:'Jonas'}],
        events:[{title:'Swim meet',icon:'🏊',date:day(2),start:'16:30',end:'18:00',all_day:false,source:'Swim club',category:'sport_activity'},{title:'Class trip day',icon:'🚌',date:day(5),start:null,end:null,all_day:true,source:'School calendar',category:'school_care'}],
        events_state:'available'}; })(),
    bag:{available:true,days:[],items:[{id:'b1',subject:'Sport',label:'Sports kit',by:'parent'},{id:'b2',subject:'Sport',label:'Water bottle',by:'child'},{id:'b3',subject:'Maths',label:'Geometry set',by:'parent'},
      {id:'b4',subject:'Biology',label:'Textbook',by:'child'},{id:'b5',subject:'Swimming',label:'Swim bag',by:'parent'},{id:'b6',subject:'Swimming',label:'Towel',by:'parent'},{id:'b7',subject:'Music',label:'Recorder',by:'child'}],subjects:[]},
    grades:{subjects,overall:+(subjects.reduce((s,x)=>s+x.average,0)/subjects.length).toFixed(2),weights:{core_written_pct:50,minor_written_pct:30,elective_written_pct:20}},
    health:{meds:[{name:'Vitamin D',dose:'1 drop with breakfast',time:'07:30',reminds:'Nina',due_today:true,status:'given',week:Array.from({length:7},(_,i)=>wk(i))},
                  {name:'Allergy tablet',dose:'1 tablet after dinner',time:'19:00',reminds:'Jonas',due_today:true,status:null,week:Array.from({length:7},(_,i)=>wk(i))}]},
  };
})();

const isStandalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);

