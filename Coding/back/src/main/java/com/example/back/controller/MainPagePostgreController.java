package com.example.back.controller;

import com.example.back.dto.exchange.ExchangeDto;
import com.example.back.service.MainPagePostgreService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/postgre")
public class MainPagePostgreController {
    private final MainPagePostgreService mainPagePostgreService;

    // 최근 30개 전체 환율 데이터 조회
    @GetMapping("/exchange/latest30")
    public List<ExchangeDto> getLatest30Exchange() {
        return mainPagePostgreService.getLatest30Exchange();
    }
}