'use strict';
(()=>{
  const $=id=>document.getElementById(id);
  const saved=localStorage.getItem('harper-server-url')||'';
  $('backendUrl').value=saved;
  let timer=null;
  const setStatus=message=>{$('backendStatus').textContent=message;};
  function creds(){
    const base=$('backendUrl').value.trim().replace(/\/+$/,'');
    if(!/^https:\/\/[a-z0-9.-]+(?::\d+)?$/i.test(base)) throw Error('https://로 시작하는 Railway 서버 주소를 입력해 주세요.');
    const token=$('backendToken').value.trim();
    if(!token) throw Error('개인 대시보드 토큰을 입력하세요.');
    localStorage.setItem('harper-server-url',base);
    return {base,token};
  }
  async function request(path,body){
    const {base,token}=creds();
    const res=await fetch(base+path,{method:body?'POST':'GET',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,cache:'no-store'});
    const data=await res.json();
    if(!res.ok) throw Error(data.error||`서버 오류 ${res.status}`);
    return data;
  }
  async function refresh(){try{
    const s=await request('/status');
    const latest=s.last_check?`최근 조회: ${s.last_check}`:'아직 조회하지 않음';
    setStatus(`상태: ${s.status} | ${s.note} | 조회 ${s.checks}회 | ${latest} | 예약 기능 ${s.live_booking_enabled?'활성':'비활성'}`);
    if(['reserved','stopped','uncertain','idle'].includes(s.status) && timer){clearInterval(timer);timer=null;}
  }catch(e){setStatus('연결 실패: '+e.message);}}
  $('searchRealTrains').addEventListener('click',async()=>{
    const button=$('searchRealTrains');
    const status=$('trainSearchStatus');
    const results=$('trainSearchResults');
    button.disabled=true;results.replaceChildren();$('train').value='';
    status.textContent='코레일 실제 열차 목록 조회 중…';
    try{
      const data=await request('/trains',{
        departure:$('from').value,arrival:$('to').value,date:$('date').value,time:$('time').value
      });
      const trains=data.trains||[];
      status.textContent=trains.length?`${trains.length}개 조회됨. 희망 열차 한 편을 선택하세요. 좌석 잔여 현황은 변경될 수 있습니다.`:'검색 조건에 맞는 열차가 없습니다. 코레일 공식 앱에서도 확인하세요.';
      for(const t of trains){
        const row=document.createElement('div');row.className='saved-item';
        row.style.marginBottom='10px';row.style.padding='12px';
        const name=document.createElement('div');
        const title=document.createElement('strong');title.textContent=`${t.departure_time||'?'} → ${t.arrival_time||'?'} · ${t.train_no}호`;
        const desc=document.createElement('p');desc.className='hint';desc.textContent=`${t.train_type||'열차'} | 일반실: ${t.general} | 특실: ${t.special}`;
        name.append(title,desc);
        const choose=document.createElement('button');choose.type='button';choose.className='secondary';choose.textContent='이 열차 예약 희망';
        choose.addEventListener('click',()=>{
          $('train').value=t.train_no;
          results.querySelectorAll('button').forEach(b=>{b.textContent='이 열차 예약 희망';b.disabled=false;});
          choose.textContent='선택됨 ✓';choose.disabled=true;
          status.textContent=`선택 완료: ${t.train_no}호 (${t.departure_time} 출발). 감시를 시작하려면 아래 “1석 감시 시작”을 사용하세요.`;
        });
        row.append(name,choose);results.append(row);
      }
    }catch(e){status.textContent='실제 열차 조회 실패: '+e.message;}
    finally{button.disabled=false;}
  });
  $('backendStart').addEventListener('click',async()=>{
    try{
      if(!$('bookingConsent').checked)throw Error('실제 1석 예약 동의에 체크해 주세요.');
      if(!/^\d{1,5}$/.test($('train').value.trim()))throw Error('먼저 실제 열차 검색 결과에서 예약 희망 열차를 선택하세요.');
      if($('count').value!=='1')throw Error('자동 감시는 성인 1명만 지원합니다.');
      const req={departure:$('from').value,arrival:$('to').value,date:$('date').value,time:$('time').value,train_no:$('train').value.trim(),seat:$('class').value,consent:true};
      setStatus('서버에 감시 시작을 요청하는 중…');
      const response=await request('/start',req);setStatus(response.note);
      if(timer) clearInterval(timer);timer=setInterval(refresh,10000);await refresh();
    }catch(e){setStatus('시작 실패: '+e.message);}
  });
  $('backendStop').addEventListener('click',async()=>{try{const r=await request('/stop',{});setStatus(r.note);await refresh();}catch(e){setStatus('중지 실패: '+e.message);}});
  $('backendRefresh').addEventListener('click',refresh);
})();
