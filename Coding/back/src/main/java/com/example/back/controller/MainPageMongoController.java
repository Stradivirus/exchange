package com.example.back.controller;

import com.example.back.service.MainPageMongoService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/mongo")
public class MainPageMongoController {
    private final MainPageMongoService mainPageMongoService;

    @GetMapping("/latest")
    public com.example.back.dto.MainPageResponseDto getLatestMainPageInfo() {
        return mainPageMongoService.getLatestMainPageInfo();
    }
}
