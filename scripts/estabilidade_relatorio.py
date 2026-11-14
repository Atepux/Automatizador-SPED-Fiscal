"""Motor independente de UI: prontidao do botao nao prova atualizacao."""
import time


class SinalConteudoIndisponivel(RuntimeError):
    pass


def aguardar_estabilidade(amostrar, inicial, alterado, timeout=10, janela_estavel=.75,
                         clock=time.monotonic, pause=time.sleep, registrar=lambda **kw:None):
    if timeout<=0 or janela_estavel<=0 or janela_estavel>=timeout:
        raise ValueError('prazos_invalidos')
    baseline=inicial.get('conteudo_token')
    if not baseline:raise SinalConteudoIndisponivel('conteudo_inicial_nao_observavel')
    deadline=clock()+timeout
    seen_loading=False;transition=False;signature=None;stable_since=None;count=0
    last={}
    while clock()<deadline:
        observation=amostrar()  # Falhas de leitura propagam; nao reutilizar ultima amostra.
        now=clock()
        if now>=deadline:break
        last=observation
        token=observation.get('conteudo_token')
        present=observation.get('conteudo_presente') is True and bool(token)
        loading=observation.get('carregando')
        seen_loading |= loading is True
        if present and loading is False and (token!=baseline or seen_loading):transition=True
        ready=(observation.get('checked') is True and observation.get('salvar_habilitado') is True
               and present and loading is False and (not alterado or transition))
        registrar(checked=observation.get('checked') is True,salvar_habilitado=observation.get('salvar_habilitado') is True,
                  conteudo_observavel=present,carregando=loading,transicao_observada=transition)
        if ready:
            if token!=signature:signature=token;stable_since=now;count=1
            else:count+=1
            if count>=3 and now-stable_since>=janela_estavel:
                return {'final':True,'checked':True,'estabilidade_confirmada':True,'salvar_habilitado':True,
                        'atualizacao_confirmada':not alterado or transition,'sinal_conteudo_validado':True,
                        'transicao_observada':transition,'busy_observado':seen_loading,
                        'amostras_estaveis':count,'intervalo_estavel_s':round(now-stable_since,4)}
        else:signature=None;stable_since=None;count=0
        pause(min(.25,max(0,deadline-clock())))
    reason=('checkbox_nao_confirmado' if last.get('checked') is not True else
            'atualizacao_nao_confirmada' if alterado and not transition else 'conteudo_nao_estavel')
    raise TimeoutError(reason)
