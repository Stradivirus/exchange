package com.example.back.mongo.mental;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface EconomicSentimentRepository extends MongoRepository<EconomicSentiment, String> {
    EconomicSentiment findTopByOrderByDateDesc();
}
