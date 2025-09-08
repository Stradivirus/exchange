package com.example.back.service;

import com.example.back.dto.exchange.ExchangeDto;
import com.example.back.entity.exchange.Exchange;
import com.example.back.repository.exchange.ExchangeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MainPagePostgreService {
    private final ExchangeRepository exchangeRepository;

    // 최근 30개 전체 환율 데이터 조회
    public List<ExchangeDto> getLatest30Exchange() {
        List<Exchange> exchangeList = exchangeRepository.findTop30ByOrderByDateDesc();
        return exchangeList.stream()
                .map(e -> ExchangeDto.builder()
                        .date(e.getDate())
                        .usd(e.getUsd())
                        .jpy(e.getJpy())
                        .eur(e.getEur())
                        .cny(e.getCny())
                        .build())
                .collect(Collectors.toList());
    }
}