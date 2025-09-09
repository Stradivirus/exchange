package com.example.back.mongo.mental;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface ConsumerSentimentRepository extends MongoRepository<ConsumerSentiment, String> {
    ConsumerSentiment findTopByOrderByDateDesc();
}
