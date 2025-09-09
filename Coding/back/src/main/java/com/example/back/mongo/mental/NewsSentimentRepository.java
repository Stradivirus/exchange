package com.example.back.mongo.mental;

import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface NewsSentimentRepository extends MongoRepository<NewsSentiment, String> {
    NewsSentiment findTopByOrderByDateDesc();
    List<NewsSentiment> findTop5ByOrderByDateDesc();
}
