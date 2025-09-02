package com.example.back.controller;

import com.example.back.dto.DailyExchangeResponse;
import com.example.back.service.DailyExchangeService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import org.springframework.web.bind.annotation.PathVariable;
import java.time.LocalDate;

@RestController
@RequestMapping("/api/daily-exchange")
@RequiredArgsConstructor
public class DailyExchangeController {
    private final DailyExchangeService dailyExchangeService;

    @GetMapping("/latest")
    public DailyExchangeResponse getLatestDailyExchange() {
        return dailyExchangeService.getLatestDailyExchange();
    }

    @GetMapping("/{date}")
    public DailyExchangeResponse getDailyExchangeByDate(@PathVariable String date) {
        // yyyy-MM-dd 형식으로 들어옴
        return dailyExchangeService.getDailyExchangeByDate(LocalDate.parse(date));
    }
}
