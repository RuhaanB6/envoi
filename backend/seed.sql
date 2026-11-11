-- Repeatable demo data; rerunning restores deleted seed letters.
SELECT pg_advisory_xact_lock(3482026);
INSERT INTO users(username,email,display_name) VALUES
('ruhaan', 'ruhaan@example.test', 'Ruhaan'),
('maya', 'maya@example.test', 'Maya'),
('leo', 'leo@example.test', 'Leo'),
('nora', 'nora@example.test', 'Nora'),
('aisha', 'aisha@example.test', 'Aisha')
ON CONFLICT (username) DO NOTHING;
INSERT INTO penpalships(user_a_id,user_b_id) SELECT a.id,b.id FROM users a,users b WHERE a.username='ruhaan' AND b.username='maya' ON CONFLICT (user_a_id,user_b_id) DO NOTHING;
INSERT INTO penpalships(user_a_id,user_b_id) SELECT a.id,b.id FROM users a,users b WHERE a.username='ruhaan' AND b.username='leo' ON CONFLICT (user_a_id,user_b_id) DO NOTHING;
INSERT INTO penpalships(user_a_id,user_b_id) SELECT a.id,b.id FROM users a,users b WHERE a.username='ruhaan' AND b.username='aisha' ON CONFLICT (user_a_id,user_b_id) DO NOTHING;
INSERT INTO penpalships(user_a_id,user_b_id) SELECT a.id,b.id FROM users a,users b WHERE a.username='maya' AND b.username='nora' ON CONFLICT (user_a_id,user_b_id) DO NOTHING;
INSERT INTO penpalships(user_a_id,user_b_id) SELECT a.id,b.id FROM users a,users b WHERE a.username='leo' AND b.username='nora' ON CONFLICT (user_a_id,user_b_id) DO NOTHING;

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'A quiet morning','I found a quiet corner on campus today. It reminded me of our last conversation.','direct','draft',now()-interval '25 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='ruhaan' AND b.username='nora'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A quiet morning');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'Notes from campus','Thank you for the book recommendation. I finished the first chapter and already have questions.

There is more to tell.','penpal','delivered',now()-interval '24 days',now()-interval '24 days',now()-interval '23 days',now()-interval '23 days'
FROM users a,users b WHERE a.username='leo' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Notes from campus');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'The book you mentioned','The weather changed overnight. I hope your week has been kind to you. Write when you can.

There is more to tell. There is more to tell.','penpal','in_transit',now()-interval '23 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='ruhaan' AND b.username='aisha'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='The book you mentioned');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'Rain on the windows','I found a quiet corner on campus today. It reminded me of our last conversation.

There is more to tell. There is more to tell. There is more to tell.','direct','draft',now()-interval '22 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='aisha' AND b.username='maya'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Rain on the windows');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'An autumn walk','Thank you for the book recommendation. I finished the first chapter and already have questions.','penpal','delivered',now()-interval '21 days',now()-interval '21 days',now()-interval '20 days',now()-interval '20 days'
FROM users a,users b WHERE a.username='leo' AND b.username='nora'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='An autumn walk');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'A small discovery','The weather changed overnight. I hope your week has been kind to you. Write when you can.

There is more to tell.','penpal','in_transit',now()-interval '20 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='maya' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A small discovery');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'Your last postcard','I found a quiet corner on campus today. It reminded me of our last conversation.

There is more to tell. There is more to tell.','direct','draft',now()-interval '19 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='leo' AND b.username='aisha'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Your last postcard');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'Plans for the weekend','Thank you for the book recommendation. I finished the first chapter and already have questions.

There is more to tell. There is more to tell. There is more to tell.','penpal','delivered',now()-interval '18 days',now()-interval '18 days',now()-interval '17 days',now()-interval '17 days'
FROM users a,users b WHERE a.username='aisha' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Plans for the weekend');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'A favorite recipe','The weather changed overnight. I hope your week has been kind to you. Write when you can.','penpal','in_transit',now()-interval '17 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='maya' AND b.username='nora'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A favorite recipe');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'After the concert','I found a quiet corner on campus today. It reminded me of our last conversation.

There is more to tell.','direct','draft',now()-interval '16 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='nora' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='After the concert');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'Something to remember','Thank you for the book recommendation. I finished the first chapter and already have questions.

There is more to tell. There is more to tell.','penpal','delivered',now()-interval '15 days',now()-interval '15 days',now()-interval '14 days',now()-interval '14 days'
FROM users a,users b WHERE a.username='ruhaan' AND b.username='maya'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Something to remember');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'From the library','The weather changed overnight. I hope your week has been kind to you. Write when you can.

There is more to tell. There is more to tell. There is more to tell.','penpal','in_transit',now()-interval '14 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='leo' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='From the library');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'A new beginning','I found a quiet corner on campus today. It reminded me of our last conversation.','direct','draft',now()-interval '13 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='maya' AND b.username='aisha'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A new beginning');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'The long way home','Thank you for the book recommendation. I finished the first chapter and already have questions.

There is more to tell.','penpal','delivered',now()-interval '12 days',now()-interval '12 days',now()-interval '11 days',now()-interval '11 days'
FROM users a,users b WHERE a.username='nora' AND b.username='maya'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='The long way home');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'Coffee on Wednesday','The weather changed overnight. I hope your week has been kind to you. Write when you can.

There is more to tell. There is more to tell.','penpal','in_transit',now()-interval '11 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='leo' AND b.username='nora'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Coffee on Wednesday');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,NULL,'A little good news','I found a quiet corner on campus today. It reminded me of our last conversation.

There is more to tell. There is more to tell. There is more to tell.','direct','draft',now()-interval '10 days',NULL,NULL,NULL
FROM users a,users b WHERE a.username='aisha' AND b.username='leo'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A little good news');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'A question for you','Thank you for the book recommendation. I finished the first chapter and already have questions.','penpal','delivered',now()-interval '9 days',now()-interval '9 days',now()-interval '8 days',now()-interval '8 days'
FROM users a,users b WHERE a.username='ruhaan' AND b.username='leo'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='A question for you');

INSERT INTO letters(sender_id,recipient_id,penpalship_id,subject,body,mode,status,created_at,send_at,deliver_at,delivered_at)
SELECT a.id,b.id,(SELECT id FROM penpalships WHERE user_a_id=least(a.id,b.id) AND user_b_id=greatest(a.id,b.id)),'Until next time','The weather changed overnight. I hope your week has been kind to you. Write when you can.

There is more to tell.','penpal','in_transit',now()-interval '8 days',now()-interval '3 days',now()+interval '1 day',NULL
FROM users a,users b WHERE a.username='aisha' AND b.username='ruhaan'
AND NOT EXISTS (SELECT 1 FROM letters WHERE sender_id=a.id AND recipient_id=b.id AND subject='Until next time');
